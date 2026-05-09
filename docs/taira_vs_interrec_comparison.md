# TAIRA Baseline 与 InterRec/MCMIPL 比较分析文档

> 生成时间：2026-05-09  
> 作者：复现 baseline 过程中整理

---

## 一、核心问题：TAIRA 无法直接在 CRS 数据集上比较

### 1.1 三种方法的任务范式对比

| 维度 | TAIRA | MCMIPL | **InterRec（我们的方法）** |
|------|-------|--------|--------------------------|
| 任务类型 | LLM 多智能体检索推荐 | 知识图谱 + RL 多轮对话推荐 | Bayesian 信念 + LLM 多轮对话推荐 |
| 输入 | 用户文本 query（预先写好）| 用户历史交互 items | 用户历史交互 items |
| 过程 | 一次 LLM 规划 → 检索 → 推荐 | 多轮提问 attribute → 缩小候选集 → 推荐 | 多轮提问 intent hypothesis → Bayesian 更新 → 推荐 |
| 数据集 | Amazon（clothing / beauty / music）| LAST_FM_STAR / YELP_STAR / BOOK / MOVIE | LastFM（hetrec2011）|
| 评估指标 | HR@10, NDCG@10 | SR@5/10/15, AvgT, hDCG | HR@10, NDCG@10, MRR@10 |
| "成功"定义 | top-10 推荐包含目标 item | K 轮内推荐包含目标 item | top-10 推荐包含目标 item |

### 1.2 为什么不能直接比较

**TAIRA 的本质**：给定一段自然语言 query（如"我想找适合户外烧烤的音乐"），通过 LLM 规划 → Searcher + ItemRetrieval → Interactor 生成一个推荐列表。**全程只有一轮推荐**，没有"提问"用户再"更新"的过程。

**MCMIPL/InterRec 的本质**：给定用户历史交互记录，通过多轮对话（"你喜欢 Pop 还是 Rock？"）逐步锁定用户偏好，最终在 K 轮内推荐目标 item。**SR@K 指的是在 K 轮对话预算内成功推荐的用户比例**。

因此：
- TAIRA 没有"多轮对话"过程，无法自然地产生 SR@K 指标（它始终是"1轮"完成）
- MCMIPL/InterRec 的 SR@15=0.903 和 TAIRA 的 HR@10=0.477 描述的是完全不同的东西

---

## 二、所有评估指标的含义

### 2.1 MCMIPL/InterRec 使用的 CRS 指标

| 指标 | 全称 | 含义 | 越高/低越好 |
|------|------|------|------------|
| **SR@5** | Success Rate @ 5 turns | 在 5 轮对话以内，成功推荐目标 item 的用户比例 | 越高越好 |
| **SR@10** | Success Rate @ 10 turns | 在 10 轮以内成功的用户比例 | 越高越好 |
| **SR@15** | Success Rate @ 15 turns | 在 15 轮（最大轮数）以内成功的用户比例，**主指标** | 越高越好 |
| **AvgT** | Average Turns | 成功案例的平均对话轮数 | **越低越好**（越少轮数越高效）|
| **hDCG** | hit-rate weighted DCG | 命中时目标 item 在推荐列表中的排名加权折扣增益 | 越高越好 |

**SR@K 的直觉**：想象 100 个用户每人都有想找的 item，系统和用户多轮对话，SR@15=0.9 意味着 90 个用户在 15 轮以内被成功推荐到。

**AvgT 的直觉**：那 90 个成功的用户平均花了几轮对话？越少说明系统越"聪明"，能快速锁定偏好。

**hDCG 的直觉**：成功推荐时，目标 item 排在第 1 位和第 10 位是不同质量的，hDCG 对排名靠前的成功给予更高奖励。

**SR@5 vs SR@15 的差值**：反映系统的"早期提问效率"。MCMIPL 的 SR@5=0.45 而 SR@15=0.90，差值=0.45 说明很多成功案例需要 6-15 轮才能完成，系统早期效率不足。**InterRec 的一个优势就是能提升 SR@5，减少这个差值。**

### 2.2 TAIRA 使用的推荐质量指标

| 指标 | 含义 | 说明 |
|------|------|------|
| **HR@10** | Hit Rate @ 10 | 目标 items 中被召回进 top-10 的比例（近似 Recall@10）|
| **MRR@10** | Mean Reciprocal Rank | 第一个命中目标 item 的排名倒数 |
| **NDCG@10** | Normalized DCG @ 10 | 考虑相关性得分和排名位置的归一化折扣增益 |
| **SR (success rate)** | 成功率 | 至少有 1 个目标 item 在推荐结果中（= HR@10 > 0 且评估器判定有效）|

---

## 三、为什么当前 TAIRA 跑的 amazon_music 无法用于主表

1. **数据集不同**：TAIRA 跑的是 amazon_music，InterRec 跑的是 LastFM，MCMIPL 跑的是 LAST_FM_STAR（另一种格式的 LastFM 变体）
2. **指标不可比**：HR@10 ≠ SR@15，即使数值相近，含义完全不同
3. **任务不同**：TAIRA 的 query 是预先写好的文本，不是从用户历史生成的

---

## 四、实现公平比较的可行路径

### 方案 A：在同一数据集上对齐（**推荐方案**）

将 TAIRA 适配到 **InterRec 已有的 LastFM 数据格式**，在相同数据集上评估，使用 HR@10 / SR 作为共同指标。

**具体步骤**（本机 LastFM 数据已有，可立即执行）：

```
现有数据 (interrec/data/processed/):
  sessions.json    → 每个用户的 observed_history + future_test (目标 items)
  items.csv        → item_id, title, artist_name, tags, description
```

**数据转换**：
```python
# 对每个 test session：
# 1. 从目标 item 的 description/tags 生成自然语言 query
#    （用 DeepSeek: "Write a music search query for artist: X, tags: gothic darkwave..."）
# 2. 将此 query 写入 query_data1.csv 的 new_query 列
# 3. 将目标 item ID 写入 targets 列
# 4. 将用户历史 items 的描述汇总写入 preferences 列
```

**评估对齐**：使用 HR@10（TAIRA 自然产出）和 SR（hit_rate > 0）对比 InterRec 的 HR@10。

**预期工作量**：约 2-3 小时编写数据转换脚本 + 运行实验。

### 方案 B：在 MCMIPL 的 CRS 数据集上运行（需下载数据）

MCMIPL 的 LAST_FM_STAR 等数据集当前**不在本机上**，且网络不可用，暂时无法执行。

需要：
1. 下载 MCMIPL 官方数据（GitHub: XuhuiRen/MCMIPL）
2. 将 CRS 格式（user-item-attribute graph）转换为 TAIRA 格式
3. 对 TAIRA 实现 SR@K 指标（记录每轮后的 top-K 推荐）

### 方案 C：TAIRA 计算 SR 指标、在 Amazon 数据集上比较

用 TAIRA 当前的 amazon_music 结果（SR=0.928）作为一个参考点，但这与 MCMIPL/InterRec 的数据集完全不同，**不能放入同一行进行直接比较**，只能作为补充实验。

---

## 五、推荐的主表结构（对齐后）

```
数据集: LastFM（所有方法统一使用）
最大轮数: 15（或 InterRec 使用的轮数）

方法              | SR@5 | SR@10 | SR@15 | AvgT  | HR@10 | NDCG@10
─────────────────────────────────────────────────────────────────────
MCMIPL            | 0.450| 0.817 | 0.903 | 6.723 |  -    |  -
                  |±0.043|±0.033 |±0.017 |±0.370 |       |
BM25 Baseline     |  -   |  -    |  -    |  -    | 0.200 | 0.068
TAIRA†            |  -   |  -    | ~SR   |  -    | TBD   | TBD
                  （需在 LastFM 数据上重新运行）
InterRec（ours）  | TBD  | TBD   | TBD   | TBD   | TBD   | TBD
```

**† TAIRA 注脚**：TAIRA 原设计为单轮 LLM 规划推荐，无原生多轮对话机制，SR 等于 HR@10 > 0 的比例（单次推荐成功率），AvgT = 1（固定单轮）。BM25 + DeepSeek-chat 替代官方 BGE-M3 + GPT-4o。

---

## 六、立即可以执行的事项

### 已完成
- [x] TAIRA 在 amazon_music 上跑通（3 seeds，SR=0.928，HR@10=0.477，NDCG@10=0.744）
- [x] 发现并修复 2 个关键 bug（PlannerAgent 非末位、ID 行号误读）

### 需要确认再执行
- [ ] **确认主表使用哪个数据集**（LastFM? 还是 Amazon?）
- [ ] **确认是否需要 TAIRA 产出 SR@K**（需要说明其单轮特性）
- [ ] 如需 LastFM 对齐：编写 `convert_lastfm_to_taira.py` 数据转换脚本（2-3h）
- [ ] 如需 MCMIPL 数据集：需要先下载数据

---

## 七、方法核心差异总结表（用于论文 Related Work / Method 部分）

| 对比维度 | TAIRA | MCMIPL | **InterRec（ours）** |
|----------|-------|--------|---------------------|
| 偏好建模 | 无显式偏好模型，LLM 直接规划 | 知识图谱 + GCN embedding | **贝叶斯高斯分布 N(μ, Σ)** |
| 提问机制 | 无（单次推荐）| MCQ 选择题（固定 attribute 选项）| **动态 intent hypothesis（LLM 生成）** |
| "应不应该问"的决策 | 无 | RL（DQN）策略网络 | **信息增益 VOI 决策（可解释）** |
| 问什么 | N/A | 预定义 attribute 池中选择 | **LLM 从不确定性方向动态生成假设** |
| 用户回答后如何更新 | N/A | 排除不符合的候选 | **Laplace 近似 Bayesian 后验更新** |
| 需要 LLM API | ✅ 是（每条 query 8-15 次调用）| ❌ 否（纯 RL + KG）| ✅ 是（每轮 3-5 次调用）|
| 计算复杂度 | 高（LLM 规划 + 多 Agent）| 中（RL 训练需数十小时）| 中（Bayesian 推断 + LLM per turn）|
| 可解释性 | 中（LLM 推理链可追溯）| 低（黑盒 RL 策略）| **高（Bayesian belief 可视化，IG 可解释）** |
| 原始评测数据集 | Amazon（clothing/beauty/music）| LastFM-star / Yelp-star / Book / Movie | LastFM（hetrec2011）|
