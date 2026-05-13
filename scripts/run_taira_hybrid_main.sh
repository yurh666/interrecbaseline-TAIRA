#!/usr/bin/env bash
# Run TAIRA main.py with hybrid retrieval:
#   - After SearcherAgent → ItemRetrieval uses BM25 (CPU) unless fallback needs BGE.
#   - Otherwise → BGE dense + rerank (GPU when available).
#
# Prerequisite: project_embeddings.npy for DOMAIN if any BGE path runs (precompute or fallback).
# Typical: set TAIRA_EMBEDDINGS_ROOT to data disk; export OPENAI_* per utils/task.py
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT/TAIRA"
exec python3 main.py "$@"
