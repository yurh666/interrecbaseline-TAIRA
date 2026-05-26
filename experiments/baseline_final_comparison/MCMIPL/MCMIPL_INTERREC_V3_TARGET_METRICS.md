# InterRec / v3 — Targets vs MCMIPL（自动生成 / 受限声明）

JSON 账本：`MCMIPL_interrec_v3_target_metrics.json`

---

## Quality

| 档位 | Target | Numeric? |
|------|--------|----------|
| **A Minimum acceptable** | 与 MCMIPL **`SR10_CRS`（CRS 评测）同一 handler**下，不出现「定义偷换」。 | **cannot set numeric**：NDCG/MRR 缺同口径观测。 |
| **B Paper-ready** | HR@10 或 CRS-SR@10「桥接声明」下同域 **≥** seed-聚合基线或对差异给出显著性脚注。 | 待定（需对齐 evaluator）。 |
| **C Strong** | LastFM/MovieLens/Yelp（三域全）至少在 **两项**可比 quality 维度领先。 | 当前 Yelp **MCMIPL 未完成**。 |

## Interaction

| 档位 | Target |
|------|--------|
| **A/B** | 明确披露 **AvgT≠TAIRA Ask**；若对齐 MCQ 「question turn」计数需人工定义 extractor。 |

## Cost / Efficiency

MCMIPL Phase B：**无 LLM**。  
若以 **wall-time / CPU-hour** story 讨论：双方需结构化记录总训练+推理账本。

---

**若 baseline Yelp 未完：** `cannot set numeric strong target`。
