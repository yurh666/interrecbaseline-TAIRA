> **【已并入主报告】** 对齐表与结论见 **`TAIRA_FINAL_REPORT.md`** §5。

# TAIRA vs InterRec / `frontier_clustered_v32` — 实验设置对齐审计

**前提：** 本机工作区内 **未发现** InterRec/v3 的 `run_summary.json`、`full_log.jsonl`、或 `frontier_clustered_v32` 跑分目录（已粗搜 `~/experiments`）。因此对 **「InterRec 侧的事实设置」**，大量维度只能标为 **`unknown`**。以下 **Baseline_setting** 以 `TAIRA/system_config.yaml`、`scripts/parse_taira_metrics.py`、与各 `results/metrics/run_*.json` 脚注为准。

## 结论：**`mostly comparable with caveats` → 更接近 `partially comparable`**

在非补齐参考跑分与配对 session manifest 的前提下，更稳妥的结论为：

> **`partially comparable`**：**可在「同一预处理域数据集 + Top-10 + 同源 future_test」下讨论趋势**；但若将 **TAIRA 的单轮 LLM 评估 HR@NDCG/MRR** 与 **InterRec 多轮累积 SR@K** 直接作为「同一主指标」并列，则 **不公平**。

若未来提供 **完全相同的 test session 列表**、并约定 **InterRec 侧只报第 1 轮推荐质量** 或 **TAIRA 扩展为多轮**，可升级为 **`mostly comparable with caveats`**。

## 哪些指标 **不能**在未说明时与 InterRec/v3 直接比

1. **多轮 `SR@5` / `SR@10` / `SR@15`（CRS 成功至第 K 轮）** — TAIRA 无多轮过程；仅能通过 `main_table_interrec_paradigm` 用 **HR@10 代理 SR@K**（LLM 判分），语义不同。  
2. **`AvgT` / `hDCG`（多轮对话式定义）** — TAIRA 将 `AvgT` 固化为 1、`hDCG` 用 `NDCG@10` 填表，**仅为版式对齐**，非 MCMIPL 原公式。  
3. **`avg_ask_count` / `ask_rate` / VOI 相关** — TAIRA **无用户提问闭环**，无法与 InterRec 的交互效率指标对称比较。  
4. **成本类（tokens / wall time / HTTP 次数）** — 基线侧 **未落盘**，与 v3 的成本对比 **暂不可量化**。  
5. **若主表采用 `direct_*`（ID 硬命中）** — TAIRA 在 Amazon 上 **接近 0**，与 LLM 列 **数量级不同**；须 **独立子表** 呈现，不可与 LLM 列混排而不加脚注。

## 逐维 CSV

见 `TAIRA_setting_alignment_audit.csv`。
