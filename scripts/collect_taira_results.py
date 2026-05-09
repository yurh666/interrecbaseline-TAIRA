#!/usr/bin/env python3
"""
Collect TAIRA per-seed metrics JSONs and write to comparison/results/taira_results.csv.
Also writes mean ± std summary.

Usage:
    cd taira_official
    python scripts/collect_taira_results.py
"""
import json
import csv
import glob
import os
import statistics
from pathlib import Path


METRIC_DIR = Path(__file__).parent.parent / "results" / "metrics"
OUT_DIR = Path(__file__).parent.parent.parent.parent / "comparison" / "results"


def collect():
    json_files = sorted(METRIC_DIR.glob("run_*_seed*.json"))
    if not json_files:
        print(f"No metric JSONs found in {METRIC_DIR}")
        return

    rows = []
    for f in json_files:
        stem = f.stem  # e.g. run_amazon_music_seed0
        parts = stem.split("_")
        seed_str = parts[-1]  # seed0
        seed = int(seed_str.replace("seed", ""))
        domain = "_".join(parts[1:-1])  # amazon_music
        m = json.loads(f.read_text())
        rows.append({
            "method": "TAIRA",
            "dataset": domain,
            "seed": seed,
            "SR": m.get("SR", ""),
            "HR@10": m.get("HR@10", ""),
            "MRR@10": m.get("MRR@10", ""),
            "NDCG@10": m.get("NDCG@10", ""),
            "HR@10_succ": m.get("HR@10_succ", ""),
            "NDCG@10_succ": m.get("NDCG@10_succ", ""),
            "fail_rate": m.get("fail_rate", ""),
            "n_queries": m.get("n_queries", ""),
            "n_success": m.get("n_success", ""),
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / "taira_results.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"Written {len(rows)} rows to {out_csv}")

    # Summary: mean ± std per domain
    from collections import defaultdict
    by_domain = defaultdict(list)
    for r in rows:
        by_domain[r["dataset"]].append(r)

    print("\n=== Summary (mean ± std) ===")
    for domain, domain_rows in by_domain.items():
        print(f"\nDomain: {domain} (n_seeds={len(domain_rows)})")
        for metric in ["SR", "HR@10", "MRR@10", "NDCG@10", "fail_rate"]:
            vals = [float(r[metric]) for r in domain_rows if r[metric] != ""]
            if vals:
                mean = statistics.mean(vals)
                std = statistics.stdev(vals) if len(vals) > 1 else 0.0
                print(f"  {metric}: {mean:.4f} ± {std:.4f}")


if __name__ == "__main__":
    collect()
