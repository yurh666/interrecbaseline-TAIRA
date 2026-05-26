# MCMIPL — Completeness Check（只读日志，无重跑）

**BASELINE_NAME**：MCMIPL（仓库：`interrecbaseline-MCMIPL`）  
**读取时间**：基于工作区现有 `train_*.log`、`phase_b_cpu_master_20260516.log` 的离线检查。

## 实际读取的数据源路径（任务 1）

| 类型 | 路径 |
|------|------|
| Phase B 汇总 / 续跑痕迹 | `/home/yrh666/interrecbaseline-MCMIPL/main_table_experiments/logs/phase_b_cpu_master_20260516.log` |
| BOOK×3 | `.../logs/train_BOOK_s{0,1,2}.log` |
| MOVIE×3 | `.../logs/train_MOVIE_s{0,1,2}.log` |
| LAST_FM×3 | `.../logs/train_LAST_FM_STAR_s{0,1,2}.log` |
| YELP×3 | `.../logs/train_YELP_STAR_s{0,1,2}.log` |
| 官方 README / 数据集名 | `/home/yrh666/interrecbaseline-MCMIPL/main_table_experiments/baselines/mcmipl_official/MCMIPL/README.md` |

**未发现（与 Prompt 模板一致）：**  
`run_summary.json`、`full_log.jsonl`、`metrics.csv`（InterRec/TIRA 范式）、结构化 `comparison.md`。

## 检查结论概要

| 检查项 | 结论 |
|--------|------|
| `run_summary.json` / `full_log.jsonl` | **不存在**：本 baseline 仅存 **tee 训练日志**。 |
| `metrics.csv` 统一范式 | **不存在**。 |
| Traceback（抽检 tail / grep） | 本轮有效 BOOK/MOVIE/LAST_FM 段落 **未发现典型 Python Traceback footer**（不代表零风险）。 |
| seed | **明示**：每条 `train_*` 头部 `seed=`。 |
| dataset / split | **README**：BOOK=Amazon-Book，`MOVIE` 对应 README 所写 MovieLens，`LAST_FM_STAR`、`YELP_STAR`。**非** TAIRA CSV 的会话 manifest split。 |
| max_turn | `run_mcmipl.sh` 传参 `--max_turn 15`。 |
| `n_sessions / completed_n_sessions` | RL 范式与 InterRec manifest **不同**：日志未给出「completed_n_sessions」。 |
| `ask_count / turn_count` | 评测行含 **`AvgT`（平均轮次长度）**，**不等于** Prompt 定义的 `avg_ask_count`。 |
| wall time / API | **未**在日志中以结构化字段汇总总墙钟；Phase B CPU **无 HTTP**。 |
| incomplete session | Yelp **本轮 Pipeline 不完整**（见 CSV）。MOVIE seed=1：存在 DONE 混入 tqdm 行的痕迹，但未捕获 `best!!!!!!!!` **最终评测行**。 |

## 分项完成度（与 InterRec 「run 工件」类比）

| 域（MCMIPL） | TAIRA 主表近似列 | Seeds 完成情况 | 可用于「最终均值±std」 |
|---------------|----------------|----------------|--------------------------|
| `LAST_FM_STAR` | LastFM | DONE×3（含续跑成功后） | **SR10_CRS 三 seed ±std**：可 |
| `MOVIE` | MovieLens | DONE×3（日志语义） | **仅 seed0+2** 有可解析 SR10 |
| `YELP_STAR` | Yelp | 本轮 **未完**（s0 无 DONE；其余时间戳陈旧） | **不可**填入主对比表 |
| `BOOK`（额外） | 不在三列表 | DONE×3 | 可用于附录而非 TAIRA triple 列 |

## 工件导出

- 明细：`MCMIPL_completeness_check.csv`
