#!/usr/bin/env bash
# Phase 2: run TAIRA main experiments after TAIRA/data/<DOMAIN>/project_embeddings.npy exists.
# Usage:
#   export OPENAI_API_KEY=...
#   export PYTHONHASHSEED=0
#   ./scripts/run_taira_after_bge_embeddings.sh lastfm
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN="${1:?usage: $0 <domain e.g. lastfm>}"

CFG="$REPO_ROOT/TAIRA/system_config.yaml"
NPY="$REPO_ROOT/TAIRA/data/$DOMAIN/project_embeddings.npy"
MAN="$REPO_ROOT/TAIRA/data/$DOMAIN/bge_embedding_manifest.json"

if [[ ! -f "$NPY" || ! -f "$MAN" ]]; then
  echo "ERROR: Missing BGE artifacts for domain=$DOMAIN"
  echo "  expected: $NPY"
  echo "  expected: $MAN"
  exit 2
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "WARNING: OPENAI_API_KEY is empty; set it for LLM calls."
fi

# Point YAML DOMAIN at the requested domain (simple sed; keep other keys)
if command -v python3 >/dev/null 2>&1; then
  python3 - <<PY
import pathlib, re
p = pathlib.Path("$CFG")
text = p.read_text()
text = re.sub(r'^DOMAIN:\\s*\"[^\"]*\"', f'DOMAIN: "{DOMAIN}"', text, flags=re.M)
p.write_text(text)
print("Updated DOMAIN in", p)
PY
else
  echo "ERROR: python3 needed to patch DOMAIN in system_config.yaml"
  exit 3
fi

cd "$REPO_ROOT/TAIRA"
exec python3 main.py
