# MCMIPL — Setting Alignment Audit（对照 InterRec / frontier_clustered_v3）

## 全局结论标签

**`partially comparable`（分项：若干维度 `partial` / `not directly comparable` / `unknown`）**

若非完成 **同源 test users、candidate pool、evaluation handler** 的桥接，**不得**把 TAIRA triple 表中 `SR@10/NDCG@10/MRR@10` 与 MCMIPL 日志 SR10 视作同一格子。

---

## 逐项比对（节选）

详见 `MCMIPL_setting_alignment_audit.csv`。要点：

### Dataset / Catalog

| 维度 | TAIRA / v3 期望 | MCMIPL 实际 |
|------|-----------------|-------------|
| 数据域 | CSV 四域：`lastfm`、`movielens`、`yelp`… | README：`lastfm_star`、`MOVIE`、`yelp_star`、`BOOK`。**MovieLens≈MOVIE**。 |
| Manifest | TAIRA JSON 会话 | MCMIPL SCPR 数据处理 + CRS 采样用户；未见与 TAIRA manifest 对齐表。 |

### Interaction

| 维度 | TAIRA Ask | MCMIPL |
|------|-----------|--------|
| 显性偏好提问 | TAIRA：`Ask≡0` | 交互为 **multiple-choice attribute questions**，与「澄清问答」措辞不同。**AvgT≠avg_ask_count**。 |

### Model / Embedding

MCMIPL：**TransE + DGL/GNN + Offline RL**。无 LLM 生成式 Top-K。**与 TAIRA BM25/LLM 路径本质不同**，只能作为 **「另一类强 CRS baseline」**，不是「同源 LLM 排序器」对照。

---

## 「哪些指标不能公平比」摘要

1. **`SR10`：** TAIRA 「`HR@10` LLM-eval」≠ MCMIPL 「CRS SR10」。  
2. **`NDCG@10`/`MRR@10`：** MCMIPL **未在同一日志提供**，禁止把 `Rank` 误标为此二项。  
3. **成本：** TAIRA tokens vs MCMIPL CPU-hours — **可比性仅限叙述层**，不作数值比值。

---

导出：`MCMIPL_setting_alignment_audit.csv`。
