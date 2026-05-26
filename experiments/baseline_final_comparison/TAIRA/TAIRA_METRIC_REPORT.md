> **【已并入主报告】** 完整内容与逐 seed 表见 **`TAIRA_FINAL_REPORT.md`**。

# TAIRA — 指标统一口径说明（对齐 InterRec / v3）

**数据源：** `results/taira_results.csv`、`results/metrics/run_*.json`、`scripts/parse_taira_metrics.py` 注释、`EXPERIMENT_SUMMARY.md`。

## 两套「命中」语义（请勿混用）

1. **`HR@10` / `NDCG@10` / `MRR@10`（主 CSV 默认列）**  
   - TAIRA CSV 字段 `hit_rate` 被视为 **Recall@10 风格** 的均值后聚合（见解析脚本注释），但数值来自管线中的 **LLM 评估**。  
   - **不得**在多轮 CRS 语境下直接与「第 K 轮内首次成功」的 **SR@K** 字面等同。

2. **`direct_HR@10` / `direct_MRR@10` / `direct_NDCG@10`**（亦称 `protocol_interrec_item_id`）  
   - **推荐列表中的 item ID 是否与 `future_test` 集合在 Top-10 相交** — 与仓库文档所述 **「与 InterRec method1 硬协议最接近」** 的路线。  
   - 表中 **Recall@10** 主列填入 **HR@10** 仅表示「与 TAIRA LLM Recall@10 列对齐」；若论文主对比走 ID 协议，应以 **`direct_*`** 单列报告。

## 与「SR@K」的桥梁（仅作脚注/表脚注）

仓库在 `run_*.json` 的 **`main_table_interrec_paradigm`** 中为单轮 TAIRA 约定：**`SR@5 = SR@10 = SR@15 = HR@10`（均由 LLM 评估）**，`AvgT = 1`，`hDCG = NDCG@10`。  
这与多轮 Dialogue CRS 里的 **首轮即成功概率**可有讨论空间，但若 InterRec/v3 的 SR@K 是 **多轮累积成功**，数值上 **不可在未说明的情况下并排宣称「同一 SR 定义」**。

## Ranking / Recommendation quality — 摘录

以下为 **CSV 原生列**；下列指标 **not available**：`HitRate@1`、`HitRate@5`（单列）、`Recall@5`、`NDCG@5`、`MRR@5`、`Recall@20`、`NDCG@20`、`MRR@20`、`preference_error`。

粗汇总（mean ± std，三 seed）：见 `results/EXPERIMENT_SUMMARY.md`。  
要点：**Yelp `fail_rate` 超 56%**，主表的「质量均值」必须与 **覆盖率/失败会话**脚注同时出现。

## Interaction metrics — 摘录

TAIRA：**单轮**，无 CRS 语义下的 **`ask_rate` / `zero_ask_rate` / early_stop`。  
占位对齐：`avg_turn_count = 1.0`（与 `main_AvgT` 一致）；**`avg_ask_count = 0`**。

## Cost / efficiency — 摘录

- **`wall_time_*`、`LLM HTTP count`、`tokens`：** **not available**。  
  **补齐：** 在每 query 打点写 JSON；或对 LLM 客户端统一计量。

## Stability

- **每域 3 seeds** — mean ± std 可用。  
- **paired Miss→Hit：** **not available**。

细粒度表格见：`TAIRA_metric_table.csv`、`TAIRA_metric_table.json`。
