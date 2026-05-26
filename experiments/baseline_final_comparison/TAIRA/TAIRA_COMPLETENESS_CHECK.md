> **【已并入主报告】** 完整内容与表格见 **`TAIRA_FINAL_REPORT.md`**（本文档仅供历史/拆分存档）。

# TAIRA baseline — 完整性检查（Completeness）

**BASELINE_NAME:** TAIRA  
**分析范围：** 仅 TAIRA（InterRec / `frontier_clustered_v32` 参考跑分目录在本工作区未找到）。

## 本次实际读取的文件路径

| 类别 | 路径 |
|------|------|
| 汇总结果 CSV | `/home/yrh666/interrecbaseline-TAIRA/results/taira_results.csv` |
| 逐 run 指标 JSON（12 份） | `/home/yrh666/interrecbaseline-TAIRA/results/metrics/run_{amazon_book,lastfm,movielens,yelp}_seed{0,1,2}.json` |
| 汇总 Markdown | `/home/yrh666/interrecbaseline-TAIRA/results/EXPERIMENT_SUMMARY.md` |
| 系统配置（只读） | `/home/yrh666/interrecbaseline-TAIRA/TAIRA/system_config.yaml` |
| 指标解析说明 | `/home/yrh666/interrecbaseline-TAIRA/scripts/parse_taira_metrics.py` |
| 方法/协议文档 | `/home/yrh666/interrecbaseline-TAIRA/docs/taira_reproduction_report.md`, `docs/taira_vs_interrec_comparison.md` |
| 部分运行日志（抽检错误模式） | `/home/yrh666/interrecbaseline-TAIRA/results/three_domains_20260520_154627.log`（含多条 `Traceback` / `JSONDecodeError`）、`resume_serial_20260526_115555.log` |

**未发现（已搜索）：** 工作区 `$HOME/experiments/**` 下无 `run_summary.json`、`full_log.jsonl`、`frontier_clustered_v32`、`comparison.md`、`diagnostics.json` 等与本任务模板一致的 InterRec/v3 参考产物。

## 检查清单结论

| 检查项 | 结论 |
|--------|------|
| `run_dir` / 可追溯产物是否存在 | ✅ 各路 `seed_*` 下存在检查点 CSV 与日志，例如 `/home/yrh666/interrecbaseline-TAIRA/results/checkpoints/<dataset>/seed_<n>/result-TAIRA.csv` |
| `run_summary.json` | ❌ **不存在** — 若以该文件为必选 gate，需在 InterRec/v3 pipeline 对齐后补齐 |
| `full_log.jsonl` | ❌ **不存在** — 仅有分散的 `*.log`、`log_*.log` |
| `metrics` / comparison 是否存在 | ✅ `results/taira_results.csv`、`results/metrics/run_*.json`、`EXPERIMENT_SUMMARY.md`；无独立 `comparison.md` |
| tracebacks / errors / timeout | ⚠️ 历史日志中存在 **`JSONDecodeError`（模型输出非严格 JSON）** 及对应 `fail`/`fail_rate`；未对全部 log 做穷尽统计 |
| `n_sessions` / `completed_n_sessions` | ✅ 可由 `n_queries`（等价于本仓库统计行数）、`n_success` 反映；⚠️ 与配置的 `QUERY_NUMBER: 500` 不完全一致：`lastfm`、`movielens` 等为 **\<500**，与「按 id 续跑 / 重复 id」等已知工程行为一致 |
| seed | ✅ `taira_results.csv` 与 `run_*_seed*.json` 中均有 `seed 0–2` |
| dataset / split | ⚠️ 配置与文档表明为 **InterRec 对齐格式的域数据 + `QUERY_NUMBER` 截断测试子集**；**训练/验证集路径未在本次读取的 JSON/CSV 中显式校验** |
| max_turns | ⚠️ 本范式为 **单轮 TAIRA**，无多轮 CRS `max_turns`；`main_table_interrec_paradigm` 将 `AvgT` 固定为 **1**（仅作表对齐用） |
| ask_count / turn_count | ⚠️ 无 CRS 语义下的 `ask_count`；等价 **平均交互轮数为 1**（无用户提问闭环） |
| wall time / API usage | ❌ **`not available`** 于已读取的 CSV/JSON 中 |
| incomplete session | ⚠️ 以 **`fail`=1（含解析失败）**与 **高 `fail_rate`（尤其 yelp）** 表征；不等价于「少跑」，但表征 **协议内未完成的成功推荐** |

## `completeness_status` 总体判断

- **Amazon Book**：行数贴近 500，`fail_rate` 约 8–10%，度量文件齐全 → **`complete_metrics_artifacts_known_failures`**  
- **LastFM**：三 seed **均为 427 行**，低于 `QUERY_NUMBER=500`，但三 seed **一致**，适合报告 **均值±std**，需在论文脚注 **会话数对齐** → **`metrics_complete_session_count_below_config_cap`**  
- **MovieLens**：三 seed **均为 397 行**，同上 → **`metrics_complete_session_count_below_config_cap`**  
- **Yelp**：492 行/seed，`fail_rate` **56–58%**，与域难度/管线稳定性相关 → **`metrics_complete_high_failure_rate`**  

详细逐行条目见：`TAIRA_completeness_check.csv`。
