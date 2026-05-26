#!/usr/bin/env python3
"""
Recompute TAIRA Recall@5 and NDCG@5 from per-query EvaluateAgent logs under
results/checkpoints/<dataset>/seed_<n>/log_<i>.log, aligned with rows of
result-TAIRA.csv (row i -> log_{i+1}.log), matching main_resume.py numbering.

Definitions (see TAIRA_FINAL_REPORT.md §0 / §4.6):
- Recall@5: 1 if max(relevance_scores[:5]) >= 1.0 else 0; missing log -> 0.
- NDCG@5: DCG/IDCG on positions 1..5 with the same discount as evaluate_agent.calculate_ndcg(..., p=5).

Usage:
  python scripts/compute_taira_recall_ndcg_at5.py [dataset ...]   # default all with checkpoints
"""
from __future__ import annotations

import csv
import glob
import math
import os
import re
import statistics
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "results", "checkpoints")

DATASETS_DEFAULT = ("lastfm", "movielens", "yelp", "amazon_book")


def extract_scores(text: str) -> list[float] | None:
    ms = list(re.finditer(r'"relevance_scores"\s*:\s*\[([^\]]+)\]', text))
    if not ms:
        return None
    nums: list[float] = []
    for part in ms[-1].group(1).split(","):
        part = part.strip()
        if part:
            try:
                nums.append(float(part))
            except ValueError:
                continue
    return nums[:10] if len(nums) >= 10 else None


def ndcg_at_p(scores: list[float], p: int) -> float:
    ranked = [float(x) for x in scores[:10]]
    dcg = sum(ranked[i] / math.log2(i + 2) for i in range(min(p, len(ranked))))
    ideal = sorted(ranked, reverse=True)
    idcg = sum(ideal[i] / math.log2(i + 2) for i in range(min(p, len(ideal))))
    return dcg / idcg if idcg > 0 else 0.0


def recall_hit_topk(scores: list[float], k: int, thresh: float = 1.0) -> float:
    head = [float(x) for x in scores[: min(k, len(scores))]]
    return 1.0 if any(x >= thresh for x in head) else 0.0


def agg_one_seed(dataset: str, seed: int) -> tuple[list[float], list[float]] | None:
    base = os.path.join(ROOT, dataset, f"seed_{seed}")
    csvp = os.path.join(base, "result-TAIRA.csv")
    if not os.path.isfile(csvp):
        return None
    with open(csvp, newline="", encoding="ISO-8859-1", errors="ignore") as f:
        rows = list(csv.DictReader(f))
    rows = [r for r in rows if r.get("id") and str(r["id"]).strip() != "mean"]
    vals_r5: list[float] = []
    vals_n5: list[float] = []
    for i, _ in enumerate(rows):
        lp = os.path.join(base, f"log_{i + 1}.log")
        if not os.path.isfile(lp):
            vals_r5.append(0.0)
            vals_n5.append(0.0)
            continue
        txt = open(lp, encoding="utf-8", errors="ignore").read()
        sc = extract_scores(txt)
        if sc is None:
            vals_r5.append(0.0)
            vals_n5.append(0.0)
            continue
        vals_r5.append(recall_hit_topk(sc, 5))
        vals_n5.append(ndcg_at_p(sc, 5))
    return vals_r5, vals_n5


def main(argv: list[str]) -> None:
    dss = argv[1:] if len(argv) > 1 else list(DATASETS_DEFAULT)
    for ds in dss:
        means_r5: list[float] = []
        means_n5: list[float] = []
        for sd in range(3):
            out = agg_one_seed(ds, sd)
            if out is None:
                continue
            r5, n5 = out
            if not r5:
                continue
            means_r5.append(statistics.mean(r5))
            means_n5.append(statistics.mean(n5))
        if not means_r5:
            print(ds, "NO_DATA (missing checkpoints or CSV)")
            continue
        mr = statistics.mean(means_r5)
        sr = statistics.stdev(means_r5) if len(means_r5) > 1 else 0.0
        mn = statistics.mean(means_n5)
        sn = statistics.stdev(means_n5) if len(means_n5) > 1 else 0.0
        print(f"{ds}: Recall@5 = {mr:.4f} ± {sr:.4f}   NDCG@5 = {mn:.4f} ± {sn:.4f}")


if __name__ == "__main__":
    main(sys.argv)
