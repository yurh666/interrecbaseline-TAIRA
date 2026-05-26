> **【已并入主报告】** 见 **`TAIRA_FINAL_REPORT.md`** §7。

# TAIRA vs InterRec / `frontier_clustered_v32` — 范式与方法差距分析

以下 **InterRec / v3 核心思想** 按用户给定提纲归纳，与本 **TAIRA 单轮 TAIRA-multi-agent baseline**对照。

## InterRec / v3（目标范式）

| 机制 | 说明 |
|------|------|
| Belief over preference | 将用户偏好表示为可被更新的分布/向量信念 |
| Bayesian / Gaussian update | （典型实现路径）对用户反馈做近似后验 |
| VOI / when-to-ask | 信息量或价值驱动是否发问 |
| Hypothesis-level questions | LLM 生成结构化假设以供用户辨析 |
| `frontier_clustered_v32` | 在当前 `belief_scores` 下抽取 Top-K/boundary frontier，经 cluster contrast **贴近排序边界发问**缓解 **entropy-VOI 与 item ranking 不对齐** |

## TAIRA vs 上述机制

| 比较点 | TAIRA |
|--------|-------|
| 直接优化 item-level ranking | 通过 LLM+B25 链路提升 Top-10 命中，但是 **隐含**而非显式学习目标 |
| 显式建模 uncertainty | **弱 / 缺失** |
| Belief update | **无 CRS 语义更新** |
| 解释为何发问 | **N/A**，不发用户疑问 |
| Question generation（假设级） | **无**CRS 结构化提问 |
| 问题与 Top-K frontier 绑定 | **无** frontier cluster 对齐机制 |
| 成本可控（可计量） | 配置显示 **多起 LLM 调用**/`TOPN_ITEMS:500`，但 **账本指标未归档** ⇒ 当前 **不可测** |
| 跨数据集迁移 | 实测四域分差大 ⇒ **实证上不稳定** |

## 分类结论

| 条目 | 判断 |
|------|------|
| **该 baseline 是强 ranking baseline 还是强 interaction baseline** | **强「单轮生成式 Ranking / Agentic Retrieval」baseline** — **非** CRS 交互式 clarification baseline |
| **InterRec / v3 必须赢它的指标（若叙事为「结构化交互物有所值」）** | 在多轮范式下：**累计成功型 `SR@K`（约定 K）、早期成功 `SR@5`、更少轮均值 `AvgT`**；若坚持用 ID-hard 协议：**`protocol_interrec_item_id.HR@10`**（TAIRA Amazon 极低，较易占优但需同源评估器） |
| **可以接近即可的指标** | 在 **仅用单轮 HR@10/NDCG@10（LLM 判）对齐**的子实验中，InterRec「不必碾压」但需要 **不慢太多**且不牺牲稳定性 |
| **应突出的优势** | **可解释的提问策略（VOI/frontier簇）**、**信念更新一致性**、**失败模式可控（低 JSON 语法崩）**、**交互效率高（成功所需轮数）** |
