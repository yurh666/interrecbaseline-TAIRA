#!/usr/bin/env python3
"""
Precompute BGE-M3 dense vectors for all items in a domain (GPU strongly recommended).
Writes:
  TAIRA/data/<domain>/project_embeddings.npy   shape (N, D), float32, L2-normalized rows
  TAIRA/data/<domain>/bge_embedding_manifest.json

Run from repository root:
  cd /path/to/interrecbaseline-TAIRA
  python scripts/precompute_bge_embeddings.py --domain lastfm --batch-size 32

Use --all-interrec-domains for: lastfm, yelp, movielens, amazon_book
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAIRA_ROOT = os.path.join(REPO_ROOT, "TAIRA")
if TAIRA_ROOT not in sys.path:
    sys.path.insert(0, TAIRA_ROOT)
os.chdir(TAIRA_ROOT)

import yaml  # noqa: E402
from FlagEmbedding import BGEM3FlagModel  # noqa: E402

from utils.item_catalog import load_items_metadata  # noqa: E402


INTERREC_DOMAINS = ("lastfm", "yelp", "movielens", "amazon_book")
ALL_KNOWN = INTERREC_DOMAINS + ("amazon_clothing", "amazon_beauty", "amazon_music")


def _load_model_name() -> str:
    cfg_path = os.path.join(TAIRA_ROOT, "system_config.yaml")
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    return cfg.get("BGE_M3_MODEL", "BAAI/bge-m3")


def precompute_domain(domain: str, batch_size: int, model_name: str | None = None) -> None:
    model_name = model_name or _load_model_name()
    df = load_items_metadata(domain, domain_root="data")
    texts = df["project_info"].astype(str).tolist()
    n = len(texts)
    if n == 0:
        raise RuntimeError(f"No rows for domain={domain}")

    print(f"[{domain}] Loading {model_name} …")
    use_fp16 = True
    try:
        import torch

        if not torch.cuda.is_available():
            use_fp16 = False
            print(f"[{domain}] CUDA not available; use_fp16=False (slower on CPU).")
    except Exception:
        use_fp16 = False

    model = BGEM3FlagModel(model_name, use_fp16=use_fp16)

    vecs: list[np.ndarray] = []
    for start in range(0, n, batch_size):
        batch = texts[start : start + batch_size]
        out = model.encode(batch, batch_size=min(batch_size, len(batch)))
        dense = out["dense_vecs"]
        vecs.append(np.asarray(dense, dtype=np.float32))

    emb = np.vstack(vecs)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1e-12
    emb = emb / norms

    out_npy = os.path.join("data", domain, "project_embeddings.npy")
    np.save(out_npy, emb)

    manifest = {
        "domain": domain,
        "model": model_name,
        "n_items": int(emb.shape[0]),
        "embedding_dim": int(emb.shape[1]),
        "dtype": "float32",
        "l2_normalized_rows": True,
        "source": "scripts/precompute_bge_embeddings.py",
    }
    man_path = os.path.join("data", domain, "bge_embedding_manifest.json")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[{domain}] wrote {out_npy} shape={emb.shape}, manifest={man_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", action="append", dest="domains", help="Repeatable.")
    ap.add_argument(
        "--all-interrec-domains",
        action="store_true",
        help=f"Shortcut for {INTERREC_DOMAINS}",
    )
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--model", default=None, help="Override BGE-M3 id (default: system_config BGE_M3_MODEL).")
    args = ap.parse_args()

    if args.all_interrec_domains:
        doms = list(INTERREC_DOMAINS)
    elif args.domains:
        doms = args.domains
    else:
        ap.error("Provide --domain … (repeatable) or --all-interrec-domains")

    for d in doms:
        if d not in ALL_KNOWN:
            print(f"Warning: domain {d} not in known list {ALL_KNOWN}; continuing anyway.")
        precompute_domain(d, batch_size=args.batch_size, model_name=args.model)


if __name__ == "__main__":
    main()
