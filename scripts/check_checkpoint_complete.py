#!/usr/bin/env python3
"""
Exit 0 iff checkpoint CSV has one row per expected query (classification==1, same filter as main.py).

Usage:
  python scripts/check_checkpoint_complete.py <domain> <checkpoint_csv>

Reads QUERY_NUMBER from TAIRA/system_config.yaml (repo root = parent of scripts/).
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: check_checkpoint_complete.py <domain> <checkpoint_csv>", file=sys.stderr)
        sys.exit(2)

    domain = sys.argv[1]
    ckpt = Path(sys.argv[2]).resolve()
    repo = _repo_root()
    cfg_path = repo / "TAIRA" / "system_config.yaml"
    if not cfg_path.is_file():
        print(f"missing {cfg_path}", file=sys.stderr)
        sys.exit(2)

    cfg = yaml.safe_load(cfg_path.read_text())
    query_number = int(cfg.get("QUERY_NUMBER", 500))

    qcsv = repo / "TAIRA" / "data" / domain / "query_data1.csv"
    if not qcsv.is_file():
        print(f"missing {qcsv}", file=sys.stderr)
        sys.exit(2)

    import pandas as pd

    df = pd.read_csv(qcsv, encoding="ISO-8859-1").head(query_number)
    df = df[df["classification"] == 1]
    expected = len(df)
    if expected == 0:
        print("no queries after filter", file=sys.stderr)
        sys.exit(1)

    if not ckpt.is_file():
        sys.exit(1)

    done = pd.read_csv(ckpt, encoding="ISO-8859-1")
    if "id" not in done.columns:
        sys.exit(1)
    n_done = int(done["id"].notna().sum())

    if n_done >= expected:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
