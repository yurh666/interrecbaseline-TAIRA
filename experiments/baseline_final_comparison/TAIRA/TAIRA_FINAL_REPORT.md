# TAIRA Baseline — 汇总报告（单文件完整版）

> **用法：** 本文为 **TAIRA baseline 分析与对比结论的唯一主入口**（关键信息已全部收拢于此）。  
> 同目录下 `TAIRA_COMPLETENESS_CHECK.md`、`TAIRA_METRIC_REPORT.md`、`TAIRA_setting_alignment_audit.csv` 等为 **分项副本 / 表格导出**，按需用于脚本或审稿材料即可。

---

## 目录

0. [核心主表（LastFM / MovieLens / Yelp）](#0-核心主表lastfm--movielens--yelp)  
1. [实际读取的数据源路径](#1-实际读取的数据源路径)  
2. [Executive summary](#2-executive-summary)  
3. [跑完与否与完整性](#3-跑完与否与完整性-run-completeness)  
4. [指标口径与结果](#4-指标口径与结果-metric-results)  
5. [与 InterRec / frontier_clustered_v3 的 Setting 对齐](#5-与-interrec--frontier_clustered_v3-的-setting-对齐)  
6. [TAIRA 方法摘要（中文）](#6-taira-方法摘要中文)  
7. [与 InterRec / v3 的方法差距](#7-与-interrec--v3-的方法差距)  
8. [InterRec / v3 相对 TAIRA 的目标线](#8-interrec--v3-相对-taira-的目标线)  
9. [Paper-readiness 规则](#9-paper-readiness-规则)  
10. [Remaining gaps 与 Next actions](#10-remaining-gaps-与-next-actions)  
11. [速览 bullet（终端级）](#11-速览-bullet终端级)

**当前结论标签：**  
- **与 InterRec/v3 fair compare（协议层）：** `partially comparable`（见 §5）。  
- **`paper_ready_against_this_baseline`：** `not_ready`（缺 InterRec 对齐跑与会话 manifest；见 §9）。

---

## 0. 核心主表（LastFM / MovieLens / Yelp）

**箭头：** ↑ 越大越好；↓ 越小越好。**Ask** 为用户侧显性提问轮次（或你方 pipeline 的 `avg_ask_count`）。

**TAIRA 行指标约定（必读）：**

| 列族 | 含义 |
|------|------|
| **SR@5 / SR@10** | **表对齐桥接**：与本仓库 `main_table_interrec_paradigm` 一致，**`SR@5 = SR@10 = HR@10`（LLM 对整表 `hit_rate`/NDCG/MRR 的那一列）**，**不是**多轮 CRS「第 K 轮内成功」语义。 |
| **Recall@5** | **自下式重算**：对 `results/checkpoints/<域>/seed_<s>/` 中第 `i` 行 CSV 对应 `log_{i+1}.log` 内最后一条 **`relevance_scores`（长度 10）**；若前五维中 **任一 ≥ 1.0**（与 LLM 「满相关」刻度一致）则该 query 记 **1**，否则 **0**；**log 缺失或无法解析**时记 **0**。再对 query 取平均，并对 **seed 0–2** 报告 **mean ± std**（seed 间 std）。 |
| **NDCG@5** | **自下式重算**：对同一 `relevance_scores` 向量，取 **前 5 个位置**按 `TAIRA/user_simulate/evaluate_agent.py::calculate_ndcg` 的折扣公式计算；**log 缺失或无法解析**记 **0**。再 mean over queries，**mean ± std across seeds**。 |
| **NDCG@10 / MRR@10** | `taira_results.csv` 聚合（LLM 列）。 |
| **Ask** | TAIRA **无**用户侧澄清提问 → **0.00 ± 0.00**。 |

> **重要：** 同一行里 **SR@5（桥接）≠ Recall@5（二值命中）≠ HR@10（连续型 hit_rate 聚合）**，三者不可混读；并排是为与 CRS 文献表头对齐 + 补足 Top‑5 粒度。

数值来源：**SR*/NDCG@10/MRR@10** 来自 `results/EXPERIMENT_SUMMARY.md`；**Recall@5 / NDCG@5** 来自本机 **`results/checkpoints/`**（**未入库 Git**；若在仅有 `results/metrics/` 的机器上打开本报告，应重新跑下方脚本或对日志归档后再算）。

### Markdown 主表

| Method | LF SR@5 ↑ | LF Recall@5 ↑ | LF NDCG@5 ↑ | LF SR@10 ↑ | LF NDCG@10 ↑ | LF MRR@10 ↑ | LF Ask ↓ | ML SR@5 ↑ | ML Recall@5 ↑ | ML NDCG@5 ↑ | ML SR@10 ↑ | ML NDCG@10 ↑ | ML MRR@10 ↑ | ML Ask ↓ | Y SR@5 ↑ | Y Recall@5 ↑ | Y NDCG@5 ↑ | Y SR@10 ↑ | Y NDCG@10 ↑ | Y MRR@10 ↑ | Y Ask ↓ |
|--------|-----------|---------------|-------------|------------|--------------|-------------|----------|-----------|----------------|-------------|-------------|--------------|-------------|----------|----------|---------------|-------------|-----------|--------------|-------------|----------|
| MCMIPL | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| TAIRA | 0.7224 ± 0.0123 | 0.7814 ± 0.0049 | 0.7128 ± 0.0068 | 0.7224 ± 0.0123 | 0.8705 ± 0.0057 | 0.9214 ± 0.0024 | 0.00 ± 0.00 | 0.4774 ± 0.0026 | 0.5038 ± 0.0067 | 0.4297 ± 0.0177 | 0.4774 ± 0.0026 | 0.6117 ± 0.0134 | 0.7024 ± 0.0106 | 0.00 ± 0.00 | 0.2956 ± 0.0081 | 0.3625 ± 0.0144 | 0.3037 ± 0.0082 | 0.2956 ± 0.0081 | 0.3661 ± 0.0105 | 0.4202 ± 0.0149 | 0.00 ± 0.00 |
| InterRec-v2 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| InterRec-v3 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

**列缩：** LF=LastFM，ML=MovieLens，Y=Yelp。

### Tab 分隔（便于粘贴到表格 / LaTeX）

```text
Method	LF SR@5↑	LF Recall@5↑	LF NDCG@5↑	LF SR@10↑	LF NDCG@10↑	LF MRR@10↑	LF Ask↓	ML SR@5↑	ML Recall@5↑	ML NDCG@5↑	ML SR@10↑	ML NDCG@10↑	ML MRR@10↑	ML Ask↓	Y SR@5↑	Y Recall@5↑	Y NDCG@5↑	Y SR@10↑	Y NDCG@10↑	Y MRR@10↑	Y Ask↓
MCMIPL																						
TAIRA	0.7224 ± 0.0123	0.7814 ± 0.0049	0.7128 ± 0.0068	0.7224 ± 0.0123	0.8705 ± 0.0057	0.9214 ± 0.0024	0.00 ± 0.00	0.4774 ± 0.0026	0.5038 ± 0.0067	0.4297 ± 0.0177	0.4774 ± 0.0026	0.6117 ± 0.0134	0.7024 ± 0.0106	0.00 ± 0.00	0.2956 ± 0.0081	0.3625 ± 0.0144	0.3037 ± 0.0082	0.2956 ± 0.0081	0.3661 ± 0.0105	0.4202 ± 0.0149	0.00 ± 0.00
InterRec-v2																						
InterRec-v3																						
```

---

## 1. 实际读取的数据源路径

### 已读 TAIRA 侧

| 类别 | 路径 |
|------|------|
| 汇总结果 CSV | `/home/yrh666/interrecbaseline-TAIRA/results/taira_results.csv` |
| 逐 run 指标 JSON（12 份） | `/home/yrh666/interrecbaseline-TAIRA/results/metrics/run_{amazon_book,lastfm,movielens,yelp}_seed{0,1,2}.json` |
| 汇总 Markdown | `/home/yrh666/interrecbaseline-TAIRA/results/EXPERIMENT_SUMMARY.md` |
| 系统配置 | `/home/yrh666/interrecbaseline-TAIRA/TAIRA/system_config.yaml` |
| 指标解析逻辑 | `/home/yrh666/interrecbaseline-TAIRA/scripts/parse_taira_metrics.py` |
| 方法 / 对比文档 | `docs/taira_reproduction_report.md`，`docs/taira_vs_interrec_comparison.md` |
| 抽检日志（错误模式） | `results/three_domains_20260520_154627.log`（多 `Traceback` / `JSONDecodeError`），`resume_serial_20260526_115555.log` |

### 未在本工作区发现（InterRec / v3）

- `$HOME/experiments/**` 等处 **未发现**：`run_summary.json`、`full_log.jsonl`、`frontier_clustered_v32` 命名跑分、`comparison.md`、`diagnostics.json`（与模板一致的对照 run）。

---

## 2. Executive summary

TAIRA 在本仓库已实现 **四域 × 各 3 seeds** 的 **指标落盘**（CSV + JSON + 汇总 Markdown）。方法与评估范式本质是 **「LLM 多智能体 + 在线 BM25 检索的单轮 Top-10 生成」**，**无**与用户的多轮 clarification 闭环。

**关键协议风险：** 主表里 **`HR@10`/`NDCG@10`/`MRR@10` 来自 LLM 评估链路**；同时存在 **`direct_HR@10`（item id 与 `future_test` 在 Top-10 相交）** 这一路 **与 InterRec「硬 ID」协议更接近**。两套数字 **量级可差很远（如 amazon_book LLM-hit vs id-hit），禁止混成一列不写脚注**。

**域间稳定性：** Yelp **`fail_rate` 约 56%–58%**，与 Amazon/LastFM 等域差异极大；论文主结果必须并列 **覆盖率/失败会话**。**LastFM / MovieLens 的 `n_queries` 少于配置 `QUERY_NUMBER=500`**，与 duplicate id / resume 行为相关，脚注 **会话数对齐**。

**成本：** **`wall_time`、tokens、LLM HTTP 次数**在本仓库 CSV/JSON 中 **`not available`**，无法与 InterRec 做量化成本对标（需补账本）。

**与 InterRec 公平比较：** 在 **不配对话轮次定义桥、不配 session manifest** 的前提下，整体为 **`partially comparable`**：可在「同源预处理域数据 + Top-10」层面讨论趋势，但 **不能把多轮 CRS 的 `SR@K` 与 TAIRA 单轮 LLM-HR 无定义地并排当同一主结论**。

**§0 主表补充：** 已列 **SR@5（桥接=`HR@10`）**、从检查点 **重算的 `Recall@5` / `NDCG@5`**（见 §4.6）；三者 **定义不同，禁止混读**。

---

## 3. 跑完与否与完整性（Run completeness）

### 3.1 检查结论（逐项）

| 检查项 | 结论 |
|--------|------|
| `run_dir` / 可追溯产物 | ✅ `/home/yrh666/interrecbaseline-TAIRA/results/checkpoints/<dataset>/seed_<n>/` 下有 `result-TAIRA.csv` 及 `log_*.log` |
| `run_summary.json` | ❌ **无** |
| `full_log.jsonl` | ❌ **无**（仅分散 `*.log`） |
| metrics / comparison | ✅ `taira_results.csv`、`run_*.json`、`EXPERIMENT_SUMMARY.md`；**无**独立 `comparison.md` |
| errors / traceback | ⚠️ 历史日志中有 **`JSONDecodeError`**（非严格 JSON）；`fail_rate`/`fail` 表征管线失败 |
| `n_sessions` | ✅ **`n_queries`** 可作为完成评估的会话计数；⚠️ 与 **`QUERY_NUMBER:500`** 不完全一致 |
| seeds | ✅ **0,1,2** |
| dataset / split | ⚠️ InterRec 对齐格式的测试子集 + `QUERY_NUMBER` 截断；**train/valid 路径本次未从 JSON 校验** |
| max_turns | ⚠️ **单轮**；无 CRS 多轮 `max_turns`；表对齐时 `main_AvgT=1` |
| ask / turn | **`avg_ask_count`≈0**（无用户侧提问）；**`avg_turn_count`=1** |
| wall / API | **`not available`** |
| incomplete | ⚠️ **`fail=1`** 与高 `fail_rate`（尤其 Yelp），表示 **会话内未完成成功推荐**，不等价于「没跑Job」 |

### 3.2 按 domain 的总体状态（`completeness_status`）

- **amazon_book：** 贴近 500 行，`fail_rate` ~8%–10% → **complete_metrics，已知个别失败**。  
- **lastfm：** 三 seed 均 **427** 行 < 500 → **metrics complete，会话数低于配置 cap（需脚注）**。  
- **movielens：** 三 seed 均 **397** 行 → 同上。  
- **yelp：** 492 行，**fail_rate** ~56%–58% → **metrics complete，failure 极高域**。

### 3.3 完整性明细表（与 `TAIRA_completeness_check.csv` 一致）

| dataset | seed | expected_n_sessions | completed_n_sessions | errors / notes | has_run_summary | has_full_log | has_metrics | has_latency | has_api |
|---------|-----:|--------------------:|---------------------:|---------------|:---------------:|:------------:|:-----------:|:-----------:|:-------:|
| amazon_book | 0 | 500 | 500 | fail_rate=0.082；历史 JSONDecodeError | no | no | yes | no | no |
| amazon_book | 1 | 500 | 499 | fail_rate=0.0922 | no | no | yes | no | no |
| amazon_book | 2 | 500 | 494 | fail_rate=0.0951 | no | no | yes | no | no |
| lastfm | 0–2 | 500 | **427（各 seed）** | fail≈7.7%–8.0%；n_queries<QUERY_NUMBER | no | no | yes | no | no |
| movielens | 0–2 | 500 | **397（各 seed）** | fail≈26%–30% | no | no | yes | no | no |
| yelp | 0–2 | 500 | **492（各 seed）** | fail≈56%–58% | no | no | yes | no | no |

---

## 4. 指标口径与结果（Metric results）

### 4.1 两套命中语义（禁止混用）

1. **`HR@10`、`NDCG@10`、`MRR@10`（默认主列）**  
   - 来自 **`hit_rate` 等**，按 `parse_taira_metrics.py` 视为 **Recall@10 风格的聚合均值**，但实际由 **LLM 评估链路**打分。  
   - **≠**多轮 CRS 里「在第 K 轮内首次推荐成功」的 **`SR@K`**。

2. **`direct_HR@10`、`direct_MRR@10`、`direct_NDCG@10`**（`protocol_interrec_item_id`）  
   - 推荐列表 item **ID** 与 **`future_test` id 集合在 Top-10 是否相交**。  
   - **最适合与 InterRec「物品 ID 是否出现在 Top-10」硬协议并排** — 若论文主表走这一路，必须 **单列**并可与 LLM 列 **分开展示**。

### 4.2 与 `SR@K` 的桥接（仅脚注）

JSON 中的 **`main_table_interrec_paradigm`**：**`SR@5=SR@10=SR@15=HR@10`（均由 LLM 评估）**，`AvgT=1`，`hDCG=NDCG@10`。这是 **版面/对照用约定**，不是 MCMIPL 原版多轮 hDCG。若 InterRec 报的是 **累积多轮成功**，不能与上式 **不加说明**等价。

### 4.3 汇总 CSV 未单列存档的指标

| 指标类 | 状态 |
|--------|------|
| `HitRate@1`、`HitRate@5`（单列）、`MRR@5` | **`taira_results.csv` 未报告** |
| **`Recall@5`、`NDCG@5`（自 `relevance_scores`）** | **未写入汇总 CSV**，但可对 **`results/checkpoints/.../log_{i+1}.log`** 按 §0 / §4.6 **离线重算**（检查点目录默认 **不进 Git**。） |
| Recall/NDCG/MRR@20 | **未报告** |
| `preference_error` | **无** → 需在 evaluator 补 |
| Interaction：`ask_rate`、`zero_ask_rate`（CRS 意义） | **不适用或等价退化** |
| Cost：`wall_time_*`、LLM HTTP、tokens | **`not available`** |
| Stability：paired Miss→Hit / Hit→Miss | **`not available`** |

**交互占位（对齐表用）：** `avg_ask_count=0`，`avg_turn_count=1.0`（与 CSV `main_AvgT` 一致）。

### 4.4 逐 seed 结果（来自 `taira_results.csv`）

**说明：** **`SR`** 列为 **管线成功占比** \(1−\textit{approx fail\_rate\_mean}\) **用的 `n_success/n_queries`**；**`HR@10`**等为 **LLM 评估列**。**`direct_*`** 为 **ID 硬协议**。

| dataset | seed | n_queries | SR | fail_rate | HR@10 (LLM) | NDCG@10 | MRR@10 | direct_HR@10 | direct_NDCG@10 |
|---------|-----:|----------:|---------:|-----------:|------------:|---------:|-------:|---------------:|---------------:|
| amazon_book | 0 | 500 | 0.918 | 0.082 | 0.6778 | 0.8428 | 0.9167 | 0.008 | 0.0039 |
| amazon_book | 1 | 499 | 0.9078 | 0.0922 | 0.6761 | 0.8367 | 0.9064 | 0.006 | 0.0019 |
| amazon_book | 2 | 494 | 0.9049 | 0.0951 | 0.6678 | 0.8303 | 0.9034 | 0.004 | 0.0017 |
| lastfm | 0 | 427 | 0.9204 | 0.0796 | 0.71 | 0.8647 | 0.9188 | 0.1124 | 0.0464 |
| lastfm | 1 | 427 | 0.9251 | 0.0749 | 0.7227 | 0.8708 | 0.9235 | 0.096 | 0.0515 |
| lastfm | 2 | 427 | 0.9227 | 0.0773 | 0.7346 | 0.8761 | 0.9219 | 0.0913 | 0.043 |
| movielens | 0 | 397 | 0.7028 | 0.2972 | 0.4744 | 0.5977 | 0.6911 | 0.0327 | 0.0097 |
| movielens | 1 | 397 | 0.7355 | 0.2645 | 0.4791 | 0.6245 | 0.7121 | 0.0302 | 0.0069 |
| movielens | 2 | 397 | 0.7229 | 0.2771 | 0.4788 | 0.6128 | 0.704 | 0.0277 | 0.0109 |
| yelp | 0 | 492 | 0.4431 | 0.5569 | 0.3043 | 0.3748 | 0.4318 | 0.0 | 0.0 |
| yelp | 1 | 492 | 0.437 | 0.563 | 0.2941 | 0.369 | 0.4253 | 0.0081 | 0.0013 |
| yelp | 2 | 492 | 0.4207 | 0.5793 | 0.2883 | 0.3544 | 0.4034 | 0.002 | 0.0007 |

### 4.5 按数据集 mean ± std（三 seed，`EXPERIMENT_SUMMARY.md`）

| dataset | SR (管线) mean | HR@10 (LLM) | NDCG@10 | MRR@10 | fail_rate | direct_HR@10 | main_SR@10 (=HR@10) |
|---------|----------------|------------|---------|--------|-----------|--------------|---------------------|
| amazon_book | 0.9102±0.0069 | 0.6739±0.0054 | 0.8366±0.0063 | 0.9088±0.0070 | 0.0898±0.0069 | 0.0060±0.0020 | 0.6739±0.0054 |
| lastfm | 0.9227±0.0024 | 0.7224±0.0123 | 0.8705±0.0057 | 0.9214±0.0024 | 0.0773±0.0024 | 0.0999±0.0111 | 0.7224±0.0123 |
| movielens | 0.7204±0.0165 | 0.4774±0.0026 | 0.6117±0.0134 | 0.7024±0.0106 | 0.2796±0.0165 | 0.0302±0.0025 | 0.4774±0.0026 |
| yelp | 0.4336±0.0116 | 0.2956±0.0081 | 0.3661±0.0105 | 0.4202±0.0149 | 0.5664±0.0116 | 0.0034±0.0042 | 0.2956±0.0081 |

### 4.6 LastFM / MovieLens / Yelp：`Recall@5` 与 `NDCG@5`（检查点日志重算）

**对齐方式：** `result-TAIRA.csv` 的第 `i` 条数据行（去掉表尾均值行）对应同目录 **`log_{i+1}.log`**（见 `TAIRA/main_resume.py` 写入逻辑）。

**Recall@5：** 解析 log 内 **最后一次** `"relevance_scores": [..., 长度 10]`；若 \(\max(\text{scores}_{1..5}) \ge 1.0\) 则该 query 为 **1** 否则 **0**。**log 不存在或字段缺失 → 记 0。**

**NDCG@5：** 对上述 10 维向量，仅用 **排序位置 1–5** 的相关性取值，DCG / IDCG 与 `calculate_ndcg(..., p=5)` **同形**（IDCG 为将 **整表 10 个相关分**全局排序后的理想前五折扣和）。**缺失 → 0。**

对每个 **seed**，先在 **全体 query** 上取均值，再对 **seed 0–2** 的 seed 均值再取 **mean ± std**：

| dataset | Recall@5 ↑ mean ± std | NDCG@5 ↑ mean ± std |
|---------|----------------------|---------------------|
| lastfm | **0.7814 ± 0.0049** | **0.7128 ± 0.0068** |
| movielens | **0.5038 ± 0.0067** | **0.4297 ± 0.0177** |
| yelp | **0.3625 ± 0.0144** | **0.3037 ± 0.0082** |

**SR@5（桥）**与 §4.5 及 §0：**`SR@5 := SR@10 := HR@10`**（仍为 LLM **`hit_rate` 聚合语义**），**勿与上表 Recall@5 混读。**

复算命令（需本地存在 `results/checkpoints/`）：

```bash
python3 scripts/compute_taira_recall_ndcg_at5.py lastfm movielens yelp
```

## 5. 与 InterRec / frontier_clustered_v3 的 Setting 对齐

**前提：** InterRec 侧 **`unknown`** 居多（本地无对齐 run）。

**结论：** **`partially comparable`**。可在同源域数据 + Top-10 尺度讨论趋势；**不得**在无定义桥下把 TAIRA **`HR@10`（LLM）**与 InterRec **多轮累积 `SR@K`**当同一 headline。

### 5.1 不可以直接并排的主指标类型

1. 多轮 **`SR@5/10/15`**（CRS 成功至 K 轮） vs TAIRA 单轮 **`HR@10` 代理**  
2. 多轮 **`AvgT`/`hDCG`（CRS 原版）** vs TAIRA 表脚注固定 **`AvgT=1`、`hDCG=NDCG@10`**  
3. **`avg_ask_count`/`VOI`/when-to-ask** vs TAIRA **无发问**  
4. **tokens / wall time** vs TAIRA **`not available`**  
5. **LLM-hit 列 vs ID-hit 列** 混成一列且无脚注  

### 5.2 逐项对齐 audit（嵌入式，与 CSV 同源）

| dimension | item | InterRec_setting | Baseline_setting | aligned | fairness impact | required_action |
|-----------|------|------------------|------------------|:-------:|-----------------|-----------------|
| Dataset | bundle | workspace 未知 | amazon_book lastfm movielens yelp | unknown | high | 提供 v3 run + session manifest |
| Dataset | split | unknown | QUERY_NUMBER cap；train/valid 未核验 | unknown | medium | 导出共同 split/session 列表 |
| Sessions |同一批 test | unknown | lastfm/ml <500 rows；amazon≈500；yelp492 | unknown | high | paired session manifest |
| Seed |对齐 | Baseline 0–2 | 0–2 已存档 | partial | medium | v3 同 RNG/洗牌规则 |
| Catalog |同源目录 | unknown | YAML：BM25 在线，`TOPN_ITEMS=500`、`TOPK=10` | partial | medium | 核对 item id universe |
| Interaction |max_turns | unknown（常为 10–15） | 单次 forward | **no** | high | **定义桥**：仅第 1 轮 InterRec vs TAIRA |
| Simulator |环路 | unknown | **无交互用户闭环** | **no** | high | 子实验或扩充 TAIRA |
| Evaluation |主列口径 | unknown | LLM-hit + direct-id 双轨 | partial | **high** | **主表二选一 + 附录** |
| Logs |可追溯 | run_summary/full_log | 分散 log | **no** | medium | 统一 jsonl |

（机器粘贴版仍保留：`TAIRA_setting_alignment_audit.csv`。）

---

## 6. TAIRA 方法摘要（中文）

1. **目标：** 在历史观测下 **单轮** 生成 Top-10，使目标与未来测试 item 对齐（评估时对齐 `future_test`）。  
2. **机制：** Planner / Searcher / ItemRetrieval / Interactor；**单次 session**。  
3. **偏好：** 无显式信念；依赖 **LLM + BM25**。  
4. **主动提问：** **否**。  
5. **问题生成：** CRS 语义不适用；可有内部检索子 query。  
6. **回答更新：** **无 Bayesian / belief update**。  
7. **排序：** 检索链 + LLMInteractor；YAML **`ITEM_RETRIEVAL_RANKING_BACKEND: bm25`**。  
8. **LLM：** **强依赖**（示例 `deepseek-chat`）。  
9. **RL：** `ENABLE_LEARNING: false`。  
10. **优势：** 端到端语言能力、可解释链路（若有日志）。  
11. **短板：** JSON **解析不稳**（历史 `JSONDecodeError`）；**Yelp 域崩**；与 CRS **范式错位需脚注**。  
12. **与 InterRec/v3 最大差别：** InterRec：**信念 + VOI + 假设级发问 + frontier 簇**；TAIRA：**单轮 Agentic RAG，无 frontier 对齐问题**。

---

## 7. 与 InterRec / v3 的方法差距

| InterRec/v3 机制 | TAIRA |
|------------------|--------|
| preference belief / Bayes update | **无 CRS 信念更新** |
| VOI / when-to-ask | **不适用** |
| hypothesis-level questions | **无** |
| frontier_clustered：belief Top-K / boundary contrast | **无** |

**baseline 类型：** **强「单轮生成式 Ranking / Agentic Retrieval」** baseline；**不是**强交互 CRS baseline。

**若论文叙事「交互物有所值」：** InterRec 应在 **累积/早期 `SR@K`、`AvgT`、可追溯发问**上占优；若以 **strict ID-hit**为主列，可参考 **`direct_*`（amazon 极低）**。  
**可强调优势：** **VOI/frontier、信念一致性、发问可解释性、失败率可控叙事**。

---

## 8. InterRec / v3 相对 TAIRA 的目标线

**preference_error：** **cannot set numeric target yet**。  
**成本数值：** TAIRA **`not available`** → **暂未设 token / wall numeric target**。

对每域 TAIRA：**\(b\) = HR@10 (LLM)，\(n\) = NDCG@10，\(m\) = MRR@10**（mean）。

| 档位 | 条件（摘要） |
|------|----------------|
| **A Minimum acceptable** | 桥接 `SR@10:=HR@10` 场景： \(\ge b-0.02\)；NDCG \(\ge n-0.03\)；MRR \(\ge \max(0.92m,\, m-0.05)\)；成本账本双双补齐后再卡 **≤1.5×** |
| **B Paper-ready** | 同 setting 下 **`SR@10`桥接或 NDCG@10** 有一项 **统计显著优于** TAIRA mean；MRR 不跌破 A；JSON fallback 可比或更优；**≥3 seeds** + CI/bootstrap |
| **C Strong** | **HR、NDCG、MRR** 三者 **≥2** 项同时优于 TAIRA；成本可测时 **≤1.5×** 或减少 **≥20%** |
| **D Efficiency** | 质量满足 A **持平**时：tokens/HTTP/time **−20%+** **或** 成功所需对话轮 (**仅 InterRec 可定义**) 显著低于多轮 CRS 基线（TAIRA 无该量）

### TAIRA 参考均值（LLM 列，三 seed）

| dataset | HR@10 | NDCG@10 | MRR@10 | fail≈ |
|---------|-------|---------|--------|-------|
| amazon_book | 0.6739 | 0.8366 | 0.9088 | 0.090 |
| lastfm | 0.7224 | 0.8705 | 0.9214 | 0.077 |
| movielens | 0.4774 | 0.6117 | 0.7024 | 0.280 |
| yelp | 0.2956 | 0.3661 | 0.4202 | 0.566 |

结构化副本：`TAIRA_interrec_v3_target_metrics.json`（公式字符串与同上）。

---

## 9. Paper-readiness 规则

**`paper_ready_against_this_baseline`：** **`not_ready`**（缺对齐 InterRec run + manifest + 双侧成本账本前，无法签发）。

**升格为 `ready` 的建议 checklist（节选）：** 同 dataset / 同 test sessions / 同评估口径（明示 LLM vs ID）/`SR@10`或 NDCG@10 显著优 / **MRR 不明显跌**（容差见 §8）/ 发问与成本不误判 / malformed 率低 / **至少 1 组质性 trace**解释「为何 v3 问得更好」。

**不算赢：** **n≈5** / **setting 漂移** / 只嬴桥接 SR 但 NDCG+MRR **双崩** / 成本 **10×+**且无压缩 / **TAIRA incomplete 未脚注** / v3 **大量 fallback**

**Enum：** `not_ready`（当前）→ `weak_ready` → `ready` → `strong_ready`。细则原文仍见 `TAIRA_PAPER_READINESS_RULE.md`（与此节一致）。

---

## 10. Remaining gaps 与 Next actions

| Gaps | 补齐方式 |
|------|----------|
| 缺 InterRec v3 run + session manifest | 提供路径 + `session_id` 对齐列表 |
| `n_queries`<500（部分域） | 唯一会话键续跑或对账 CSV |
| 无 token/latency | LLM client 钩子写 metrics |
| 无 `preference_error` | evaluator 增偏好向量距离 |
| 无 paired bootstrap | A/B **同 seed** 配对重采样 |
| Recall@5 / NDCG@5 未进 `taira_results.csv` | 本地有 `results/checkpoints/` 时运行 `python3 scripts/compute_taira_recall_ndcg_at5.py`，或在 evaluator 中直接落盘 |

**Next：** (1) 提供 `frontier_clustered_v32` run；(2) 主表选定 **LLM vs ID** 主列；(3) 多轮叙事时补 **Round-1-only** InterRec 子表或扩充 TAIRA（工程大）。

---

## 11. 速览 bullet（终端级）

1. **跑完：** 四域 ×3 seed **CSV/JSON 齐全**；**无**标准化 `run_summary`/`full_log.jsonl`。  
2. **管线 SR：** Amazon ~91%，LastFM ~92%，MovieLens ~72%，Yelp ~43%（与高 fail 共存）。  
3. **核心 LLM-hit（HR@10，亦作桥接 SR@10）：** Amazon ~67%，LastFM ~72%，MovieLens ~48%，Yelp ~30%；**SR@5 桥**与其 **数值相同**。  
4. **`Recall@5` / `NDCG@5`（LastFM/Movielens/Yelp）：** 见 §0 / §4.6 **log 重算**（与 **HR@10** **不同定义**）。
5. **NDCG@10/MRR@10：** 见 §4.5 / §4.4。  
6. **Ask：** **0**（CRS）；**AvgT=1**。  
7. **成本账本：** **`not available`**。  
8. **同 setting InterRec：** **无法证实**（缺 v3 run）。  
9. **主要不一致：** 多轮 CRS vs **单轮**；**SR@K 语义**；**LLM-hit vs ID-hit**。  
10. **方法：** **多 Agent + BM25 + 单次 Top-K**。  
11. **vs InterRec 最大差别：** **无 belief/VOI/frontier question**。  
12. **最低目标：** §8-A（相对表中 mean）。  
13. **Paper-ready：** §8-B + paired 统计 + 脚注闭合。  
14. **`paper_ready_against_this_baseline`：** **`not_ready`**（缺对齐 InterRec 跑分）。  
15. **是否要补 TAIRA：** 建议至少 **会话 manifest ≤500** 与 **uniq id**脚注；不一定要全量重训。  
16. **可否直接对比：** **`partially comparable`**， headline 需谨慎。  
17. **主报告路径：** `/home/yrh666/interrecbaseline-TAIRA/experiments/baseline_final_comparison/TAIRA/TAIRA_FINAL_REPORT.md`

---

## 附录：同目录分拆文件（可选）

无需日常打开：**`TAIRA_completeness_check.csv`**、**`TAIRA_metric_table.csv`**、**`TAIRA_metric_table.json`**、**`TAIRA_setting_alignment_audit.csv`**、`TAIRA_interrec_v3_target_metrics.json`。**主题文字**已并入上文。
