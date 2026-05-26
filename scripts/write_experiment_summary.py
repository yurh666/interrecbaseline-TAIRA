#!/usr/bin/env python3
"""
Generate results/EXPERIMENT_SUMMARY.md from results/taira_results.csv
(produced by scripts/collect_taira_results.py after each domain's seeds).
"""
from __future__ import annotations

import csv
import statistics
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "results" / "taira_results.csv"
OUT_PATH = REPO_ROOT / "results" / "EXPERIMENT_SUMMARY.md"


def _git_head() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _fmt_cell(v: str) -> str:
    if v is None or v == "":
        return "—"
    try:
        return f"{float(v):.4f}"
    except ValueError:
        return str(v)


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    commit = _git_head()

    if not CSV_PATH.is_file():
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(
            f"# TAIRA 实验汇总（自动生成）\n\n"
            f"- 生成时间: {stamp}\n"
            f"- 仓库 commit: `{commit}`\n\n"
            f"尚未找到 `{CSV_PATH.relative_to(REPO_ROOT)}`。"
            f"请先完成至少一次 seed 并运行 `python scripts/collect_taira_results.py`。\n",
            encoding="utf-8",
        )
        print(f"Stub written: {OUT_PATH}")
        return

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    by_domain: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_domain[r.get("dataset", "?")].append(r)

    lines: list[str] = [
        "# TAIRA × InterRec 串行实验汇总",
        "",
        f"- 生成时间: {stamp}",
        f"- 仓库 commit: `{commit}`",
        f"- 数据源: `{CSV_PATH.relative_to(REPO_ROOT)}`（每行 = 单数据集 × 单 seed）",
        "",
        "## 各 seed 原始指标",
        "",
        "| dataset | seed | SR | HR@10 | MRR@10 | NDCG@10 | fail_rate | direct_HR@10 | interrec_id_HR@10 | interrec_id_NDCG@10 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for domain in sorted(by_domain.keys()):
        for r in sorted(by_domain[domain], key=lambda x: int(x.get("seed", 0) or 0)):
            id_ndcg = _fmt_cell(r.get("interrec_id_NDCG@10", ""))
            lines.append(
                "| {d} | {s} | {SR} | {HR} | {MRR} | {NDCG} | {fr} | {dh} | {ih} | {idn} |".format(
                    d=r.get("dataset", ""),
                    s=r.get("seed", ""),
                    SR=_fmt_cell(r.get("SR", "")),
                    HR=_fmt_cell(r.get("HR@10", "")),
                    MRR=_fmt_cell(r.get("MRR@10", "")),
                    NDCG=_fmt_cell(r.get("NDCG@10", "")),
                    fr=_fmt_cell(r.get("fail_rate", "")),
                    dh=_fmt_cell(r.get("direct_HR@10", "")),
                    ih=_fmt_cell(r.get("interrec_id_HR@10", "")),
                    idn=id_ndcg,
                )
            )

    lines.extend(
        [
            "",
            "## 按数据集 mean ± std",
            "",
        ]
    )

    numeric_cols = [
        "SR",
        "HR@10",
        "MRR@10",
        "NDCG@10",
        "fail_rate",
        "direct_HR@10",
        "interrec_id_HR@10",
        "interrec_id_NDCG@10",
        "main_SR@10",
        "main_hDCG",
    ]

    for domain in sorted(by_domain.keys()):
        lines.append(f"### `{domain}`（n_seeds={len(by_domain[domain])}）")
        lines.append("")
        for col in numeric_cols:
            vals: list[float] = []
            for r in by_domain[domain]:
                raw = r.get(col, "")
                if raw is None or raw == "":
                    continue
                try:
                    vals.append(float(raw))
                except ValueError:
                    continue
            if not vals:
                continue
            mean = statistics.mean(vals)
            std = statistics.stdev(vals) if len(vals) > 1 else 0.0
            lines.append(f"- **{col}**: {mean:.4f} ± {std:.4f}")
        lines.append("")

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Written {OUT_PATH} ({len(rows)} runs)")


if __name__ == "__main__":
    main()
