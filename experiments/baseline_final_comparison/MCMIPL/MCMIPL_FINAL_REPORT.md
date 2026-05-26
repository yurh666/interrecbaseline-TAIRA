# MCMIPL Baseline — 最终单独报告（总入口）

> **用法：** 聚合任务 1–8；含与 TAIRA prompt 对齐的「三域主表」。分项见同目录 `MCMIPL_*.md` / `.csv` / `.json`。  
> **合规：** 无 API；无重跑；无代码/配置修改；缺口标 `—` / `not available`。

---

## 0. 核心主表（LastFM / MovieLens / Yelp）

**箭头：** ↑ 越大越好；↓ 越小越好。**TAIRA Ask** 为显性提问闭环计数；**MCMIPL Ask 列暂用 `AvgT`（平均对话长度）代理**，脚注：≠ TAIRA `avg_ask_count`/`Ask=0` 语义。

### MCMIPL 填入规则（诚实口径）

- **SR@10 列：** 填入 **`SR10_CRS`**（评测路径 `dqn_evaluate`，日志 `best!!!!!!!!`），**不等价** TAIRA「`SR@10:=HR@10(LLM)`」脚注定义。  
- **NDCG@10 / MRR@10：** MCMIPL RL 日志 **不存在** IR 意义上 NDCG/MRR → 填 **—**。  
- **MovieLens：** 对齐 README 数据名 **`MOVIE`**。**seed1** 日志 **缺失最终 `best` 块** → SR10 **仅用 seed0+2**（已标注 **n=2**）。  
- **Yelp：** Phase B **`YELP_STAR`** **未完成** → **全 —**。

### Markdown 主表

| Method | LastFM SR@10 ↑ | LastFM NDCG@10 ↑ | LastFM MRR@10 ↑ | LastFM Ask ↓ | MovieLens SR@10 ↑ | MovieLens NDCG@10 ↑ | MovieLens MRR@10 ↑ | MovieLens Ask ↓ | Yelp SR@10 ↑ | Yelp NDCG@10 ↑ | Yelp MRR@10 ↑ | Yelp Ask ↓ |
|--------|----------------|------------------|-----------------|--------------|-------------------|---------------------|--------------------|-----------------|--------------|----------------|---------------|------------|
| MCMIPL | **0.5748 ± 0.0077** （SR10_CRS,n=3） | — | — | **8.183 ± 0.075** （AvgT proxy） | **0.4854 ± 0.0076** （SR10_CRS,n=2） | — | — | **10.289 ± 0.026** （AvgT,n=2） | — | — | — | — |
| TAIRA | 0.7224 ± 0.0123 | 0.8705 ± 0.0057 | 0.9214 ± 0.0024 | 0.00 ± 0.00 | 0.4774 ± 0.0026 | 0.6117 ± 0.0134 | 0.7024 ± 0.0106 | 0.00 ± 0.00 | 0.2956 ± 0.0081 | 0.3661 ± 0.0105 | 0.4202 ± 0.0149 | 0.00 ± 0.00 |
| InterRec-v2 | — | — | — | — | — | — | — | — | — | — | — | — |
| InterRec-v3 | — | — | — | — | — | — | — | — | — | — | — | — |

### Tab 分隔（粘贴用）

```
Method	LastFM SR@10 ↑	LastFM NDCG@10 ↑	LastFM MRR@10 ↑	LastFM Ask ↓	MovieLens SR@10 ↑	MovieLens NDCG@10 ↑	MovieLens MRR@10 ↑	MovieLens Ask ↓	Yelp SR@10 ↑	Yelp NDCG@10 ↑	Yelp MRR@10 ↑	Yelp Ask ↓
MCMIPL	0.5748 ± 0.0077 (SR10_CRS)	—	—	8.183 ± 0.075 (AvgT)	0.4854 ± 0.0076 (SR10_CRS,n=2)	—	—	10.289 ± 0.026 (AvgT,n=2)	—	—	—	—
TAIRA	0.7224 ± 0.0123	0.8705 ± 0.0057	0.9214 ± 0.0024	0.00 ± 0.00	0.4774 ± 0.0026	0.6117 ± 0.0134	0.7024 ± 0.0106	0.00 ± 0.00	0.2956 ± 0.0081	0.3661 ± 0.0105	0.4202 ± 0.0149	0.00 ± 0.00
InterRec-v2												
InterRec-v3												
```

---

## 1. 数据源路径（已读）

- `/home/yrh666/interrecbaseline-MCMIPL/main_table_experiments/logs/train_LAST_FM_STAR_s{0,1,2}.log`
- `/home/yrh666/interrecbaseline-MCMIPL/main_table_experiments/logs/train_MOVIE_s{0,1,2}.log`
- `/home/yrh666/interrecbaseline-MCMIPL/main_table_experiments/logs/train_BOOK_s{0,1,2}.log`
- `/home/yrh666/interrecbaseline-MCMIPL/main_table_experiments/logs/train_YELP_STAR_s{0,1,2}.log`
- `/home/yrh666/interrecbaseline-MCMIPL/main_table_experiments/logs/phase_b_cpu_master_20260516.log`
- `/home/yrh666/interrecbaseline-MCMIPL/main_table_experiments/baselines/mcmipl_official/MCMIPL/README.md`
- TAIRA 参考（只读对照，不混指标）：`/home/yrh666/interrecbaseline-TAIRA/results/taira_results.csv`

**未发现：** `run_summary.json`、`full_log.jsonl`（InterRec 模板文件）。

---

## 2. Executive summary

MCMIPL 为 WWW'22 **多兴趣 + 图谱 + RL CRS**；当前 CPU Phase B 工件为 **tee 文本日志**。可对 **LastFM** 给出 **`SR10_CRS` 三 seed 聚合**；**MovieLens(MOVIE)** 仅 **双 seed**；**Yelp** 本轮 **不可写终值**。**NDCG/MRR/LLM-cost** 在本次日志中 **systematically missing**。

---

## 3–9. 分项文件映射

| Prompt 任务 | 文件 |
|--------------|------|
| 1 Completeness | `MCMIPL_COMPLETENESS_CHECK.md`、`MCMIPL_completeness_check.csv` |
| 2 Metrics | `MCMIPL_METRIC_REPORT.md`、`MCMIPL_metric_table.csv`、`MCMIPL_metric_table.json` |
| 3 Setting audit | `MCMIPL_SETTING_ALIGNMENT_AUDIT.md`、`MCMIPL_setting_alignment_audit.csv` |
| 4 Method | `MCMIPL_METHOD_SUMMARY.md` |
| 5 Gap | `MCMIPL_VS_INTERREC_METHOD_GAP.md` |
| 6 Targets | `MCMIPL_INTERREC_V3_TARGET_METRICS.md`、`MCMIPL_interrec_v3_target_metrics.json` |
| 7 Paper rule | `MCMIPL_PAPER_READINESS_RULE.md` |

---

## 10. Remaining gaps / Next actions

| Gap | Action |
|-----|--------|
| Yelp 未完成 | 续跑 `YELP_STAR` 三 seed 至 `DONE` + `epoch-50.pkl` |
| MOVIE seed1 缺 best 行 | 改善 tee/flush 或训练末强制 JSON summary |
| NDCG/MRR 对齐 | 增加 offline session-level rank evaluator（需另授权改代码） |
| Manifest 对齐 | 固化与 TAIRA 相同 test user 列表再双方评估 |

---

## 11. 终端 bullet（12–15 条）

1. **跑完？** LastFM / BOOK /（MOVIE 有 DONE 但 seed1 指标行缺失）/ **Yelp 未完**。  
2. **核心 SR（CRS）：** LastFM **0.5748±0.0077**；MovieLens-proxy **0.4854±0.0076 (n=2)**。  
3. **Ask/cost：** 用 **AvgT** 代理；**无 LLM HTTP/tokens**。  
4. **同 setting？** **否/partial**（evaluator & session 定义不同）。  
5. **不一致点：** SR 语义、候选集、manifest、LLM 成本维度。  
6. **方法：** KG+TransE+GNN+RL + 属性 MCQ。  
7. **与 v3 最大差：** 无 belief + frontier_clustered VOI 故事链。  
8. **最低目标：** 先 **协议桥接** 再设数值线（当前 **cannot set pure numeric min**）。  
9. **paper-ready 目标：** 完成三域 + 统一 evaluator。  
10. **补跑？** **Yelp 必须**；MOVIE log **建议修**。  
11. **能直接比？** **不能**无脚注横向硬比 SR/NDCG/MRR。  
12. **`paper_ready_against_this_baseline`：** **not_ready**。  
13. **主报告路径：** 本文件。  
14. **附录 BOOK（非三列表）：** SR10_CRS mean≈**0.4009±0.0099**（三 seed）。  
15. **公平比较结论标签：** **partially comparable**（见 SETTING 审计）。

