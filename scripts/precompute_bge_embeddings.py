#!/usr/bin/env python3
"""
Precompute BGE-M3 dense vectors for all items in a domain (**CUDA required** by default; use ``--allow-cpu`` only for debugging).
Writes (under ``TAIRA_EMBEDDINGS_ROOT/<domain>/`` if that env is set, else ``TAIRA/data/<domain>/``):
  project_embeddings.npy   shape (N, D), float32, L2-normalized rows
  bge_embedding_manifest.json

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

from utils.embeddings_paths import domain_embedding_artifacts_dir  # noqa: E402
from utils.item_catalog import load_items_metadata  # noqa: E402


INTERREC_DOMAINS = ("lastfm", "yelp", "movielens", "amazon_book")
ALL_KNOWN = INTERREC_DOMAINS + ("amazon_clothing", "amazon_beauty", "amazon_music")

CANONICAL_BGE_M3 = "BAAI/bge-m3"


def _manifest_model_id(load_path: str) -> str:
    """Manifest 里固定写 ``BAAI/bge-m3``，即便权重从本机目录加载。"""
    norm = load_path.replace("\\", "/").rstrip("/")
    if norm == CANONICAL_BGE_M3 or "models--BAAI--bge-m3" in norm:
        return CANONICAL_BGE_M3
    last = os.path.basename(norm)
    if last in ("BAAI-bge-m3", "bge-m3"):
        return CANONICAL_BGE_M3
    if norm.endswith("/bge-m3"):
        return CANONICAL_BGE_M3
    return load_path


def _load_model_name() -> str:
    cfg_path = os.path.join(TAIRA_ROOT, "system_config.yaml")
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    return cfg.get("BGE_M3_MODEL", "BAAI/bge-m3")


def precompute_domain(
    domain: str,
    batch_size: int,
    model_name: str | None = None,
    *,
    allow_cpu: bool = False,
) -> None:
    model_name = model_name or _load_model_name()
    df = load_items_metadata(domain, domain_root="data")
    texts = df["project_info"].astype(str).tolist()
    n = len(texts)
    if n == 0:
        raise RuntimeError(f"No rows for domain={domain}")

    import torch

    if not torch.cuda.is_available():
        if not allow_cpu:
            raise RuntimeError(
                f"[{domain}] CUDA is required for BGE-M3 precompute (refuse CPU). "
                "Pass --allow-cpu to override (slow / not for production runs)."
            )
        print(f"[{domain}] WARNING: --allow-cpu set; encoding on CPU (very slow).")

    use_fp16 = bool(torch.cuda.is_available())
    print(f"[{domain}] Loading {model_name} … (cuda={torch.cuda.is_available()}, use_fp16={use_fp16})")

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

    art_dir = domain_embedding_artifacts_dir(domain)
    os.makedirs(art_dir, exist_ok=True)
    out_npy = os.path.join(art_dir, "project_embeddings.npy")
    np.save(out_npy, emb)

    manifest = {
        "domain": domain,
        "model": _manifest_model_id(model_name),
        "n_items": int(emb.shape[0]),
        "embedding_dim": int(emb.shape[1]),
        "dtype": "float32",
        "l2_normalized_rows": True,
        "source": "scripts/precompute_bge_embeddings.py",
    }
    man_path = os.path.join(art_dir, "bge_embedding_manifest.json")
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
    ap.add_argument(
        "--allow-cpu",
        action="store_true",
        help="Allow running without CUDA (debug only; strongly discouraged).",
    )
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
        precompute_domain(
            d,
            batch_size=args.batch_size,
            model_name=args.model,
            allow_cpu=args.allow_cpu,
        )


if __name__ == "__main__":
    main()
