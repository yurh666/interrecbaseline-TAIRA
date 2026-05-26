# MCMIPL — Metric Report（统一口径尝试 / 坦诚缺失）

## 可读指标（确有日志证据）

日志模式：`best!!!!!!!!!SR5:, SR10:, SR15:, AvgT:, Rank:`

- **`SR10`/`SR15`/`SR5`**：**MCMIPL CRS 评测路径下的成功率**，**不是** TAIRA「`SR@10 := HR@10`（LLM 评估）」那一个定义。并排主表必须用脚注拆列或改名（例如 **`SR10_CRS`**）。
- **`Rank`**：**论文式对话排序指标**，**不能**在未换算的情况下直接标为 **`MRR@10`**。
- **`AvgT`**：平均回合/步幅相关统计，**≠** 「用户显性提问次数」；与 TAIRA **`Ask:=0`** 不对等。

### 聚合（与你的三列表对齐的那部分）

#### LastFM（`LAST_FM_STAR`，seed 0–2，最终 best 行）

- **SR10_CRS**：`0.5748 ± 0.0077`（`n=3`，样本标准差）  
  单点：`[0.56675, 0.58200, 0.57550]`
- **AvgT**：`8.183 ± 0.075`（可作「交互深度 proxy」，**脚注**）

#### MovieLens（README 对齐 **`MOVIE` 数据集名**，仅 **seed 0 & 2** 可解析 SR10）

- **SR10_CRS**：`0.4854 ± 0.0076`（`n=2`） — **seed 1 缺失解析行**  
  单点：`0.4800`、`0.4908`

#### Yelp（`YELP_STAR`）

- **最终三 seed 均值**：**不可用** — 本轮 `train_YELP_STAR_s0.log` **未见 `DONE:`**；其余日志时间戳与本 Phase B **不对齐**。  
→ 主表里 **一律留空** / `not_available`。

### Amazon-Book（`BOOK`）— 附录

**SR10_CRS**：`[0.38840, 0.40760, 0.40680]` → `mean=0.4009`，`std=0.0099`  
（不入 TAIRA 「LastFM / MovieLens / Yelp」三列表。）

## 不可用 / not available（拒不伪造）

| 维度 | 原因 |
|------|------|
| **NDCG@5/10**、**MRR@5/10（IR sense）** | 训练评测日志 **未给出** IR 向量排序 NDCG/MRR。 |
| **HitRate@K（TAIRA/硬 ID）** | 需 item-level session manifest；无现成结构化文件。 |
| **LLM_HTTP / tokens** | RL 流水线 **不使用 LLM**。 |
| **wall_time_mean / p90（结构化）** | 日志未聚合；仅能人工读段落后估计，不作数值填报。 |

## 导出表格

- `MCMIPL_metric_table.csv`（宽表 + `[SR10_CRS_final,...]`）
- `MCMIPL_metric_table.json`
