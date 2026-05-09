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
    json_files = sorted(
        METRIC_DIR.glob("run_*_seed*.json")
    )
    # skip legacy names like *_seed*_old*.json / run_*_seed0_old.json
    json_files = [
        p for p in json_files
        if p.name.count("seed") == 1 and "old" not in p.stem.lower()
    ]
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
        mt = m.get("main_table_interrec_paradigm") or {}
        pid = m.get("protocol_interrec_item_id") or {}
        row = {
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
            "direct_HR@10": m.get("direct_HR@10", ""),
            "direct_MRR@10": m.get("direct_MRR@10", ""),
            "direct_NDCG@10": m.get("direct_NDCG@10", ""),
            "main_SR@5": mt.get("SR@5", ""),
            "main_SR@10": mt.get("SR@10", ""),
            "main_SR@15": mt.get("SR@15", ""),
            "main_AvgT": mt.get("AvgT", ""),
            "main_hDCG": mt.get("hDCG", ""),
            "interrec_id_HR@10": pid.get("HR@10", ""),
            "interrec_id_MRR@10": pid.get("MRR@10", ""),
            "interrec_id_NDCG@10": pid.get("NDCG@10", ""),
        }
        rows.append(row)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / "taira_results.csv"
    fieldnames = list(rows[0].keys()) if rows else []
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
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
        for metric in [
            "SR", "HR@10", "MRR@10", "NDCG@10", "fail_rate",
            "direct_HR@10",
            "main_SR@5", "main_SR@10", "main_SR@15",
            "main_hDCG", "interrec_id_HR@10",
        ]:
            vals = [float(r[metric]) for r in domain_rows if r[metric] != ""]
            if vals:
                mean = statistics.mean(vals)
                std = statistics.stdev(vals) if len(vals) > 1 else 0.0
                print(f"  {metric}: {mean:.4f} ± {std:.4f}")


if __name__ == "__main__":
    collect()
