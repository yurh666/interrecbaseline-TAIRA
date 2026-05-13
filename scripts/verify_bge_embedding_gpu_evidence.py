#!/usr/bin/env python3
"""
Reproducible checks that BGE-M3 precompute uses CUDA when available:
  - torch / GPU name
  - CUDA memory allocated after first encode (lazy GPU init in FlagEmbedding)
  - first Linear/transformer parameter device
  - optional: cosine(first_row precomputed, fresh encode of same catalog text) ~ 1

Run from repo root:
  python scripts/verify_bge_embedding_gpu_evidence.py --domain lastfm
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import torch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAIRA_ROOT = os.path.join(REPO_ROOT, "TAIRA")
sys.path.insert(0, TAIRA_ROOT)
os.chdir(TAIRA_ROOT)

from FlagEmbedding import BGEM3FlagModel  # noqa: E402

from utils.embeddings_paths import domain_embedding_artifacts_dir  # noqa: E402
from utils.item_catalog import load_items_metadata  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="lastfm")
    ap.add_argument(
        "--artifacts-root",
        default=None,
        help="Parent of <domain>/project_embeddings.npy (sets TAIRA_EMBEDDINGS_ROOT for this process).",
    )
    ap.add_argument(
        "--model-path",
        default=None,
        help="Local BGE-M3 directory or snapshot; default: env BGE_M3_LOCAL_DIR or HF hub snapshot under AUTODL_ARTIFACTS_ROOT",
    )
    args = ap.parse_args()

    if args.artifacts_root:
        os.environ["TAIRA_EMBEDDINGS_ROOT"] = os.path.abspath(args.artifacts_root)
    elif not os.environ.get("TAIRA_EMBEDDINGS_ROOT"):
        autodl_emb = "/root/autodl-tmp/interrecbaseline-TAIRA/embeddings"
        if os.path.isdir(autodl_emb):
            os.environ["TAIRA_EMBEDDINGS_ROOT"] = autodl_emb

    model_path = args.model_path
    if not model_path:
        model_path = os.environ.get("BGE_M3_LOCAL_DIR", "").strip()
    if not model_path or not os.path.isfile(os.path.join(model_path, "config.json")):
        root = os.environ.get("AUTODL_ARTIFACTS_ROOT", "/root/autodl-tmp/interrecbaseline-TAIRA")
        hub = os.path.join(root, "huggingface", "hub", "models--BAAI--bge-m3", "snapshots")
        if os.path.isdir(hub):
            snaps = sorted(os.listdir(hub))
            if snaps:
                model_path = os.path.join(hub, snaps[0])
    if not model_path or not os.path.isfile(os.path.join(model_path, "config.json")):
        raise SystemExit("Could not resolve local BGE-M3 path; pass --model-path")

    print("=== BGE-M3 GPU / consistency evidence ===")
    print("torch:", torch.__version__, "cuda_available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("device_0:", torch.cuda.get_device_name(0))

    def cuda_mem() -> int:
        return int(torch.cuda.memory_allocated(0)) if torch.cuda.is_available() else 0

    m0 = cuda_mem()
    print("\n-- Loading model --")
    model = BGEM3FlagModel(model_path, use_fp16=torch.cuda.is_available())
    m1 = cuda_mem()
    df = load_items_metadata(args.domain, domain_root="data")
    text = str(df["project_info"].iloc[0])
    print("-- First encode (lazy GPU init in typical FlagEmbedding paths) --")
    out = model.encode([text], batch_size=1)
    m2 = cuda_mem()
    param = next(model.model.parameters())
    dense = torch.as_tensor(out["dense_vecs"])
    print("output dense_vecs shape:", tuple(dense.shape), "storage device (returned tensor):", dense.device)
    print("first_parameter device:", param.device)
    print("cuda memory [bytes]: after_load delta=", m1 - m0, "after_encode delta=", m2 - m0)

    art = domain_embedding_artifacts_dir(args.domain)
    npy = os.path.join(art, "project_embeddings.npy")
    if os.path.isfile(npy):
        v = np.load(npy)[0].astype(np.float64)
        w = dense[0].float().numpy().astype(np.float64)
        v /= np.linalg.norm(v) + 1e-12
        w /= np.linalg.norm(w) + 1e-12
        cos = float(np.dot(v, w))
        print("\n-- Consistency vs", npy, "--")
        print("cosine(row0, fresh_encode text0):", cos)
        if cos < 0.99:
            raise SystemExit("Consistency check failed (expected ~1.0 for same model & normalization).")
    else:
        print("(skip npy check: not found at", npy, ")")

    if torch.cuda.is_available() and param.device.type != "cuda":
        raise SystemExit("Expected model parameters on CUDA after encode when CUDA is available.")
    if torch.cuda.is_available() and (m2 - m0) < 1_000_000:
        raise SystemExit("Expected substantial CUDA memory use after encode; got delta " + str(m2 - m0))
    print("\nOK: evidence consistent with BGE-M3 forward on CUDA for this run.")


if __name__ == "__main__":
    main()
