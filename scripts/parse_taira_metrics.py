#!/usr/bin/env python3
"""
Parse TAIRA results CSV (the incremental per-query CSV written by main.py)
into a standardized metrics JSON for use in the main comparison table.

TAIRA outputs: hit_rate (Recall@10), mrr (MRR@10, buggy=1.0 on hit),
               ndcgs (NDCG@10), fail (0/1)
These are mapped to: HR@10, MRR@10, NDCG@10, SR (success rate)

Also emits:
  - main_table_interrec_paradigm: SR@5/10/15 = HR@10 (single-turn), AvgT=1,
    hDCG = NDCG@10 (project convention; not MCMIPL's multi-turn hDCG formula).
  - protocol_interrec_item_id: direct_* columns when present — strict item-ID
    hit vs future_test in top-10; best aligned with InterRec-style ID success.

Usage:
    python parse_taira_metrics.py <result_csv> <out_json> [seed]
"""
import sys
import json
import glob
import os
from pathlib import Path


def parse_csv(csv_path: str, seed: int = 0) -> dict:
    import pandas as pd
    df = pd.read_csv(csv_path, encoding="ISO-8859-1")
    # Drop the last row which is the mean summary row (has no 'id' column value)
    df_data = df.dropna(subset=["id"]) if "id" in df.columns else df.head(-1)
    df_data = df_data[df_data["fail"].notna()].copy()
    df_data["fail"] = df_data["fail"].astype(float)

    n = len(df_data)
    success_mask = df_data["fail"] == 0
    n_success = success_mask.sum()

    metrics = {
        "seed": seed,
        "n_queries": n,
        "n_success": int(n_success),
        "SR": round(float(n_success / n), 4) if n > 0 else 0.0,
        "HR@10": round(float(df_data["hit_rate"].mean()), 4),
        "MRR@10": round(float(df_data["mrr"].mean()), 4),
        "NDCG@10": round(float(df_data["ndcgs"].mean()), 4),
        # Among successful queries only
        "HR@10_succ": round(float(df_data.loc[success_mask, "hit_rate"].mean()), 4) if n_success > 0 else 0.0,
        "NDCG@10_succ": round(float(df_data.loc[success_mask, "ndcgs"].mean()), 4) if n_success > 0 else 0.0,
        "fail_rate": round(float(df_data["fail"].mean()), 4),
    }
    if "direct_hr10" in df_data.columns:
        metrics["direct_HR@10"] = round(float(df_data["direct_hr10"].mean()), 4)
        metrics["direct_MRR@10"] = round(float(df_data["direct_mrr"].mean()), 4)
        metrics["direct_NDCG@10"] = round(float(df_data["direct_ndcg"].mean()), 4)
        metrics["protocol_interrec_item_id"] = {
            "_note": (
                "Top-10 推荐列表中的 item id 与 future_test 目标 id 集合求交；"
                "与 InterRec（method1）在同数据、同 ID 命中定义下最具可比性。"
                "（与 LLM 打分的 HR@10/NDCG 可分离报告。）"
            ),
            "HR@10": metrics["direct_HR@10"],
            "MRR@10": metrics["direct_MRR@10"],
            "NDCG@10": metrics["direct_NDCG@10"],
        }

    hr10 = metrics["HR@10"]
    ndcg10 = metrics["NDCG@10"]
    metrics["main_table_interrec_paradigm"] = {
        "_note": (
            "单轮 TAIRA：与 MCMIPL/主表「多轮 SR@K」列对齐时，SR@5=SR@10=SR@15=HR@10（LLM 评估）；"
            "AvgT 固定为 1；hDCG 列本项目约定填 NDCG@10（与对话式 hDCG 公式不同，正文需脚注）。"
        ),
        "SR@5": hr10,
        "SR@10": hr10,
        "SR@15": hr10,
        "AvgT": 1.0,
        "hDCG": ndcg10,
    }
    return metrics


def find_latest_result_csv(domain: str, log_base: str) -> str:
    pattern = os.path.join(log_base, f"TAIRA-*/result-TAIRA-*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No result CSV found in {log_base}")
    return files[-1]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <result_csv> <out_json> [seed]")
        sys.exit(1)

    csv_path = sys.argv[1]
    out_path = sys.argv[2]
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    metrics = parse_csv(csv_path, seed)
    print(json.dumps(metrics, indent=2))
    Path(out_path).write_text(json.dumps(metrics, indent=2))
    print(f"\nSaved to {out_path}")
