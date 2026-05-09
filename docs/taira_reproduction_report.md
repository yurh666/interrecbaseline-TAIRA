# TAIRA Baseline 完整复现报告

> 生成时间：2026-05-09  
> 数据集：LastFM（hetrec2011-lastfm-2k，与 InterRec 同一份数据）  
> 实验状态：🔄 **Running** — seed=0 正在运行（已完成 4/500 queries，预计 ~4.5h）

---

## 一、复现目标与定位

本实验是论文主表 **TAIRA baseline** 的复现，目的是在 **与 InterRec 完全相同的 LastFM 数据集**上获得 TAIRA 的标准性能指标，作为公平的比较基准。

### 1.1 关于数据集选择

TAIRA 原论文使用的是 Amazon 数据集（clothing / beauty / music），而 InterRec 和 MCMIPL 使用的是 LastFM 数据集。为了实现公平比较，本复现将 TAIRA **移植到 LastFM 数据集**上运行。

| 实验 | 数据集 | 状态 |
|------|--------|------|
| TAIRA (amazon_music) | Amazon Music Digital Downloads | ✅ 已完成（仅作参考，不入主表）|
| **TAIRA (lastfm)** | LastFM hetrec2011-2k（与 InterRec 同份）| 🔄 **进行中**（主表用）|
| MCMIPL | LastFM-Star（MCMIPL 官方格式）| ✅ 已完成 |
| InterRec | LastFM hetrec2011-2k | 🔄 进行中 |

---

## 二、TAIRA 方法说明与 InterRec 对比

### 2.1 任务定义对比

两种方法都在解决同一个核心问题：**给定用户过去的交互历史，帮助用户找到新的目标物品**。但实现路径完全不同：

```
TAIRA 路径:
  用户历史 → 生成文本 query → LLM 规划 → Searcher + ItemRetrieval → 推荐列表
  （整个过程：1次 LLM 规划 session，单轮推荐）

InterRec 路径:
  用户历史 → 建立 Bayesian 信念 → 多轮提问(问用户偏好) → 信念更新 → 推荐
  （整个过程：最多 15 轮对话，动态调整）
```

### 2.2 方法核心差异（论文对比维度）

| 对比维度 | TAIRA（LLM Multi-Agent）| **InterRec（我们的方法）**|
|----------|------------------------|--------------------------|
| **偏好建模机制** | 无显式偏好模型，LLM 直接规划推荐 | **贝叶斯高斯分布 N(μ, Σ)**：用历史交互初始化，每轮对话后做 Laplace 近似后验更新 |
| **是否有多轮交互** | ❌ 单轮推荐（无对话提问）| ✅ 最多 15 轮对话 |
| **提问机制** | N/A（无提问）| **动态 intent hypothesis**：LLM 从不确定性方向生成假设，用 VOI（信息增益值）决定是否提问 |
| **"问不问用户"的决策** | N/A | **信息增益决策（VOI > c_ask 才提问）**，可解释且高效 |
| **用户回答后如何更新** | N/A | **Bayesian 后验更新**：用户选择 → 对 θ* 做 Bayesian 约束更新 |
| **知识检索** | SearcherAgent 用 BM25 检索 knowledge.csv | 不使用外部知识库 |
| **物品检索** | ItemRetrievalAgent 用 BM25 检索 metadata.csv | 基于 item embedding（TF-IDF/BGE-M3）的相似度排序 |
| **LLM 的角色** | **核心**：规划、提取关键词、推荐（8-15次调用/query）| **辅助**：生成 intent hypothesis（3-5次调用/轮）|
| **可解释性** | 中（LLM 推理链可追溯）| **高**（Bayesian belief 可视化，IG 量化决策依据）|
| **计算成本** | 高（每 query 消耗 ~5000 tokens）| 中（每轮消耗 ~1500 tokens，早期成功减少总轮次）|
| **对 LLM 质量的依赖** | **高**（推荐质量直接取决于 LLM 理解能力）| **低**（Bayesian 框架提供保底，LLM 只做假设生成）|

### 2.3 对话流程对比示例

**TAIRA（单轮）**：
```
用户历史: [Radiohead, The Clash, Babyshambles, ...]
生成 query: "Can you recommend music similar to Babyshambles? I enjoy indie punk britpop."

Step 1 - PlannerAgent 规划:
  task_1: SearcherAgent → 检索 "indie punk britpop" 相关知识
  task_2: ItemRetrievalAgent → 检索匹配的 10 个 artists
  task_3: InteractorAgent → 生成最终推荐列表

最终推荐: [Babyshambles, Super Furry Animals, The Clash, ...]
评估: 目标 item (Babyshambles) 在推荐列表中 → HR@10 = 0.9
```

**InterRec（多轮）**：
```
用户历史: [Radiohead, The Clash, Babyshambles, ...]
Belief: μ = weighted avg of 历史 item embeddings

轮1 - 系统提问: "您更喜欢哪种风格？A. indie punk  B. electronic  C. metal"
用户: 选 A
→ Belief 更新: μ 向 indie punk 方向移动，σ 减小

轮2 - 推荐: [Babyshambles, Super Furry Animals, ...]
评估: 在第 2 轮推荐中命中 → SR@2=1, AvgT=2
```

---

## 三、评估指标详解

### 3.1 主表使用的指标（与 MCMIPL 对齐）

| 指标 | 全称 | 计算方式 | 含义 | 越高/低越好 |
|------|------|---------|------|------------|
| **SR@5** | Success Rate @ 5 turns | 在前 5 轮推荐中，top-10 包含 future_test item 的用户比例 | 早期快速成功能力 | ↑ 高 |
| **SR@10** | Success Rate @ 10 turns | 在前 10 轮推荐中成功的用户比例 | 中期效率 | ↑ 高 |
| **SR@15** | Success Rate @ 15 turns | 在 15 轮（上限）内成功的用户比例，**主评估指标** | 最终成功率 | ↑ 高 |
| **AvgT** | Average Turns | 成功用户的平均对话轮数（失败者=15） | 对话效率 | ↓ 低 |
| **hDCG** | hit-rate weighted DCG | `1/log2(t+3) + (1/log2(t+2) - 1/log2(t+3)) / log2(done+1)` | 考虑命中时排名和轮次的综合质量 | ↑ 高 |

**SR@K vs AvgT 的关系**：
- SR@15 = 1.0 但 AvgT = 15：系统总是最后一刻才成功，效率极低
- SR@15 = 1.0 且 AvgT = 2：系统两轮就找到目标，效率很高
- **InterRec 的优势应体现在：更高的 SR@5（早期成功）和更低的 AvgT（更少轮次）**

**TAIRA 在 SR@K 指标下的语义**（注意）：
- TAIRA 是单轮推荐系统，不做多轮对话。
- SR@K 对 TAIRA 的计算方式：**SR = 推荐列表 top-10 命中 future_test item 的用户比例**（等同于 SR@1 = HR@10）
- **TAIRA 的 SR@5=SR@10=SR@15**（单轮，命中与否只看第一次推荐）
- **TAIRA 的 AvgT = 1**（始终 1 轮，不存在多轮对话）

### 3.2 TAIRA 原生指标

| 指标 | 含义 | 计算说明 |
|------|------|---------|
| **HR@10** | Hit Rate @ 10 | TAIRA 推荐的 10 个 items 中，包含目标 artist 的比例（LLM 评判，0-1之间）|
| **MRR@10** | Mean Reciprocal Rank | 目标 artist 在推荐列表中首次出现的排名倒数 |
| **NDCG@10** | NDCG @ 10 | 考虑 artist 相关性得分和排名位置的折扣增益 |
| **SR（success rate）** | 成功率 | 推荐结果被 LLM 评估为"有效"（average(valid) > 0.5）且命中目标的比例 |

### 3.3 指标对应关系（主表填写参考）

| 主表列 | MCMIPL 来源 | TAIRA 来源 | InterRec 来源 |
|--------|------------|-----------|--------------|
| SR@5 | 官方 evaluate.py | = HR@10（单轮等价）| N/A（用 HitRate@5）|
| SR@10 | 官方 evaluate.py | = HR@10（同上）| N/A（用 HitRate@10）|
| SR@15 | 官方 evaluate.py | = HR@10（同上）| N/A（用 HitRate@10）|
| AvgT | 官方 evaluate.py | = 1（固定单轮）| avg_ask_count + 1 |
| hDCG | 官方 evaluate.py | = NDCG@10（近似）| 可计算 |
| HR@10 | ≈ SR@15 | HR@10 | HitRate@10 |
| NDCG@10 | 可计算 | NDCG@10 | NDCG@10 |

---

## 四、实验配置

### 4.1 数据适配（Patch 列表）

在原 amazon_music 系列 patches 基础上新增以下 patches：

| Patch ID | 位置 | 说明 | 影响 |
|----------|------|------|------|
| P8 | `agents/item_retrieval_agent.py` | 新增 `lastfm` domain 支持（与 `amazon_music` 共用 BM25 路径）| 无影响 |
| P9 | `user_simulate/evaluate_agent.py` | 修复 `lastfm` domain 的 `evaluate_one_recommend` 中 `exit(0)` 问题 | 关键修复 |
| P10 | `main.py` | 新增 `lastfm` domain 的 `target_product` 构建逻辑 | 无影响 |
| P11 | `scripts/convert_lastfm_to_taira.py` | 将 InterRec sessions.json 转换为 TAIRA query_data1.csv 格式 | 新增脚本 |

### 4.2 数据转换说明

```
InterRec sessions.json (1648 test sessions):
  user_id | observed_history | future_train | future_valid | future_test

↓ convert_lastfm_to_taira.py

TAIRA query_data1.csv:
  target_id | artist_title | tags(category) | query(自然语言) | preferences(历史artists)
  target_count=1 | targets=primary_future_test_id
```

**query 生成方式**（无 LLM，纯模板）：
```
"Can you recommend music similar to {target_title}? I enjoy {top6_tags} style music."
```

### 4.3 实验参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `DOMAIN` | `lastfm` | LastFM 音乐数据集 |
| `QUERY_NUMBER` | 500 | 每 seed 处理 500 个 test sessions |
| `TOPK_ITEMS` | 10 | 每次推荐 10 个 items |
| `MODEL` | `deepseek-chat` | 替代官方 GPT-4o（成本原因）|
| `seeds` | 0, 1, 2 | 3 个随机种子取均值 ± 标准差 |
| 运行总时间 | 预计 ~13.5h | 每 seed ~4.5h，3 seeds 串行 |

---

## 五、实验进展与结果

### 5.1 当前进度（实时更新）

| Seed | 状态 | 完成 queries | 预计完成时间 |
|------|------|------------|------------|
| seed=0 | 🔄 进行中 | 4/500 | ~14:30 |
| seed=1 | ⏳ 等待 | 0/500 | ~19:00 |
| seed=2 | ⏳ 等待 | 0/500 | ~24:00 |

### 5.2 早期结果（seed=0，前 4 条）

| Query | Target | HR@10 | MRR | NDCG | Fail |
|-------|--------|-------|-----|------|------|
| Babyshambles (indie punk) | 208 | 0.900 | 1.00 | 0.960 | 0 |
| The Stone Roses (90s pop) | 2606 | 0.150 | 1.00 | 0.356 | 0 |
| David Cook (american idol rock) | 297 | 0.300 | 1.00 | 0.600 | 0 |
| Rihanna (pop rnb) | 288 | 0.800 | 1.00 | 0.920 | 0 |

**早期观察**：前 4 条全部成功（SR=1.0），HR@10 均值 = 0.538，MRR = 1.0（均命中 top-1！）。

### 5.3 Amazon Music 参考结果（3 seeds，已完成，不入主表）

| 指标 | seed=0 | seed=1 | seed=2 | **均值 ± 标准差** |
|------|--------|--------|--------|-----------------|
| SR | 0.928 | 0.928 | 0.928 | **0.928 ± 0.000** |
| HR@10 | 0.483 | 0.470 | 0.478 | **0.477 ± 0.006** |
| MRR@10 | 0.908 | 0.879 | 0.887 | **0.891 ± 0.015** |
| NDCG@10 | 0.756 | 0.733 | 0.743 | **0.744 ± 0.012** |

---

## 六、主表结构预览（待完成填充）

### 6.1 统一指标说明

所有方法在 LastFM 数据集上，统一报告 **HR@10 / NDCG@10 / MRR@10** 作为共同可比指标：

```
数据集: LastFM (hetrec2011-2k, n_users=1648, n_items=2665)
评估协议: future_test 为目标 items，top-K 推荐是否命中

方法              | HR@10 | NDCG@10 | MRR@10 | SR (=HR>0) | 对话轮次
─────────────────────────────────────────────────────────────────────
BM25 Baseline     | 0.320 | 0.081   | 0.133  | ~0.xx      | N/A (1-turn)
TAIRA†            | TBD   | TBD     | TBD    | TBD        | 1 (fixed)
  (lastfm, 3seed) |       |         |        |            |
InterRec（ours）  | TBD   | TBD     | TBD    | TBD        | avg 1-15
  (lastfm, 3seed) |       |         |        |            |
```

**† TAIRA 注脚**：TAIRA 原始设计为 LLM 单轮规划推荐，无多轮对话机制。本复现使用 BM25 替代官方 BGE-M3（本地无 GPU embedding 预算），DeepSeek-chat 替代 GPT-4o，在 LastFM 数据集上运行（原论文使用 Amazon 数据集）。以上差异需在主表 caption 中注明。

### 6.2 SR@K 对比（与 MCMIPL 对齐，适用于对话系统）

若需在 SR@K 框架下比较（MCMIPL 的评估协议）：

```
方法              | SR@5  | SR@10 | SR@15 | AvgT  | hDCG
─────────────────────────────────────────────────────────
MCMIPL (lastfm-star) | 0.450 | 0.817 | 0.903 | 6.72  | 0.366
                  | ±0.043| ±0.033| ±0.017| ±0.37 | ±0.022

TAIRA† (lastfm)   | =HR@10| =HR@10| =HR@10| 1(固定)| ≈NDCG@10
  [注：单轮系统]   |       |       |       |       |

InterRec（ours）  | TBD   | TBD   | TBD   | TBD   | TBD
```

---

## 七、与 InterRec 的预期比较关系

根据已知数据和 TAIRA 早期结果推断：

**TAIRA 的相对定位**（预期）：
- TAIRA 是 LLM 规划的单轮推荐系统，HR@10 可能较高（LLM 擅长语义匹配）
- 但 TAIRA 无法做多轮偏好精炼，容易推荐"宽泛相关"而非"精确命中"
- AvgT=1 是 TAIRA 的固有局限（无对话，无法降低 AvgT）

**InterRec 的预期优势**：
1. **AvgT < 1 等价**：通过多轮对话精炼，InterRec 的 HR@10 @ turn K 可以随 K 增加而提升，而 TAIRA 固定在 1 轮
2. **精确度提升**：Bayesian 信念更新让 InterRec 能在对话后推荐更"精准"的 items（NDCG@10 更高）
3. **可解释性**：InterRec 能说明"问了什么、学到了什么、为什么推荐这些"

---

## 八、运行监控命令

```bash
# 查看实验进度
screen -S taira_lastfm -X hardcopy /tmp/s.txt && cat /tmp/s.txt

# 查看当前已完成的 query 数
LATEST=$(ls -td /root/main_table_experiments/baselines/taira_official/TAIRA/data/lastfm/logs/TAIRA-* | head -1)
ls "$LATEST" | wc -l

# 查看已保存的结果 CSV
python3 -c "
import pandas as pd
import glob, os
LATEST = sorted(glob.glob('/root/main_table_experiments/baselines/taira_official/TAIRA/data/lastfm/logs/TAIRA-*/result-*.csv'))[-1]
df = pd.read_csv(LATEST, encoding='ISO-8859-1').dropna(subset=['fail'])
n = len(df)
print(f'Completed: {n}/500 queries')
print(f'SR: {(df[\"fail\"]==0).mean():.3f}')
print(f'HR@10: {df[\"hit_rate\"].mean():.3f}')
print(f'NDCG@10: {df[\"ndcgs\"].mean():.3f}')
"
```
