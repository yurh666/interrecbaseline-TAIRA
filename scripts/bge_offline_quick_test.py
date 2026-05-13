#!/usr/bin/env python3
"""
Smoke test after embeddings exist:
  - Load project_embeddings.npy + manifest for a domain
  - Run one BGE-M3 query encode + cosine top-k
  - Run FlagReranker on a few pairs

Run from repo root:
  python scripts/bge_offline_quick_test.py --domain lastfm
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAIRA_ROOT = os.path.join(REPO_ROOT, "TAIRA")
sys.path.insert(0, TAIRA_ROOT)
os.chdir(TAIRA_ROOT)

import yaml  # noqa: E402
from FlagEmbedding import BGEM3FlagModel, FlagReranker  # noqa: E402

from utils.item_catalog import load_items_metadata  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="lastfm")
    args = ap.parse_args()
    domain = args.domain

    man_path = os.path.join("data", domain, "bge_embedding_manifest.json")
    npy_path = os.path.join("data", domain, "project_embeddings.npy")
    if not os.path.isfile(npy_path) or not os.path.isfile(man_path):
        print(f"FAIL: missing {npy_path} or {man_path}; run precompute_bge_embeddings.py first")
        sys.exit(2)

    with open(man_path) as f:
        manifest = json.load(f)
    emb = np.load(npy_path).astype(np.float32)
    if emb.shape[0] != manifest["n_items"]:
        print(f"FAIL: npy rows {emb.shape[0]} != manifest n_items {manifest['n_items']}")
        sys.exit(3)

    df = load_items_metadata(domain, domain_root="data")
    if len(df) != emb.shape[0]:
        print(f"FAIL: metadata rows {len(df)} != embedding rows {emb.shape[0]}")
        sys.exit(4)

    with open("system_config.yaml") as f:
        cfg = yaml.safe_load(f)
    bge_name = cfg.get("BGE_M3_MODEL", "BAAI/bge-m3")
    rerank_name = cfg.get("BGE_RERANKER_MODEL", "BAAI/bge-reranker-base")

    use_fp16 = True
    try:
        import torch

        if not torch.cuda.is_available():
            use_fp16 = False
    except Exception:
        use_fp16 = False

    print("Loading BGE-M3 for query encode…")
    model = BGEM3FlagModel(bge_name, use_fp16=use_fp16)
    qtext = "indie rock music similar to radiohead"
    qv = model.encode([qtext], batch_size=1)["dense_vecs"].astype(np.float32)
    qv = qv / np.linalg.norm(qv, axis=1, keepdims=True)
    scores = (emb @ qv.T).ravel()
    top5 = np.argsort(scores)[::-1][:5]
    print("Top-5 indices:", top5.tolist())
    print("Top-5 titles:", df.iloc[top5]["project_info"].str.slice(0, 80).tolist())

    print("Loading reranker…")
    reranker = FlagReranker(rerank_name, use_fp16=use_fp16)
    pairs = [[qtext, df.iloc[int(i)]["project_info"][:512]] for i in top5[:3]]
    rs = reranker.compute_score(pairs)
    print("Rerank scores (subset):", rs)

    print("OK bge_offline_quick_test passed for domain=", domain)


if __name__ == "__main__":
    main()
