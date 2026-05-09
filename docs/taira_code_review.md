# TAIRA Code Review Report

**生成时间**：2026-05-08  
**reviewer**：AI Agent (reproduction baseline)  
**repo 来源**：https://github.com/Alcein/TAIRA（手动克隆，无 git 历史）  
**论文**：Thought-Augmented Planning for LLM-Powered Interactive Recommender Agent，KDD 2026

---

## 1. Python 版本与环境

- 官方要求：Python 3.12.7+  
- 实际使用：Python 3.12.x（conda env `taira`）  
- 主要依赖：见 `TAIRA/requirements.txt`

```
FlagEmbedding==1.3.4     # BGE-M3 embedding（已替换为 BM25，见 patch notes）
fuzzywuzzy==0.18.0
nltk==3.9.1              # punkt tokenizer（已替换为 regex，见 patch notes）
openai==1.64.0           # LLM API client
pandas==2.2.3
rank_bm25==0.2.2         # BM25 检索（BM25Okapi）
sentence_transformers    # reranker（已替换，见 patch notes）
torch==2.5.1
transformers==4.48.0
```

---

## 2. 外部 API 依赖

| API | 用途 | 是否可用 | 替代方案 |
|-----|------|----------|----------|
| OpenAI-compatible LLM | 所有 Agent 的 LLM 推理 | ✅ 使用 DeepSeek | `deepseek-chat` via `api.deepseek.com/v1` |
| Google Custom Search | SearcherAgent 检索领域知识 | ❌ 不可用 | BM25 on `knowledge1.csv` |
| BGE-M3 embedding model | ItemRetrievalAgent 密集检索 | ❌ 无本地缓存 | BM25 替代 |
| bge-reranker-base | 候选重排序 | ❌ 无本地缓存 | BM25 重排 |

---

## 3. 支持的数据集

官方支持：
- `amazon_clothing`：服装推荐
- `amazon_beauty`：美妆推荐  
- `amazon_music`：音乐推荐（**本次实验使用**）

数据目录格式（每个 domain 下）：
```
data/{domain}/
  query_data1.csv    # 用户 query，含 classification/targets/preferences 等字段
  metadata.csv       # 物品 metadata（id, title, category, price, rating）
  knowledge1.csv     # 领域知识属性库（attribute, usage）
  user_profile.csv   # 用户画像（可选）
```

关键字段：
- `query_data1.csv`：`classification`（仅 ==1 的 query 参与实验）、`new_query`（增广后的用户查询）、`targets`（目标 item ASIN 列表）、`target_count`、`preferences`（用户偏好描述）
- `metadata.csv`：`id`（Amazon ASIN）、`title`、`category`
- `knowledge1.csv`：`attribute`、`usage`

---

## 4. main.py 完整运行流程

```
main.py
  ├── 读取 system_config.yaml
  ├── 加载 query_data1.csv（head(QUERY_NUMBER) → filter classification==1）
  ├── 初始化共享 agents：
  │     ItemRetrievalAgent / SearcherAgent / InteractorAgent / InterpreterAgent
  └── 对每条 query：
        ├── 创建 TAIRAManager（含 memory、target、config）
        ├── 注册 4 个 agents
        ├── manager.delegate_task()
        │     ├── Phase 1: PatternMatcher.select_best_pattern()
        │     │     └── 从 storage/thought_patterns/ 找最相似的思维模版
        │     ├── Phase 2: HierarchicalPlanner.create_initial_plan()
        │     │     └── LLM 生成 JSON 格式的子任务计划
        │     ├── Phase 3: _execute_hierarchical_plan()
        │     │     ├── 循环执行非末位子任务（SearcherAgent / ItemRetrievalAgent）
        │     │     ├── 末位任务 → InteractorAgent（生成推荐 JSON）
        │     │     │     或 PlannerAgent（触发 HierarchicalPlanner.update_plan() 重规划）
        │     │     └── EvaluateAgent.evaluate()（LLM 打分 → hit_rate/mrr/ndcg）
        │     └── Phase 4（可选）: PatternDistiller（ENABLE_LEARNING=false 时跳过）
        └── 将结果 append 到结果 CSV
```

---

## 5. Manager Agent 任务分解与 Executor Agents

### Manager Agent（HierarchicalPlanner）

职责：将用户 query 分解为结构化 JSON 子任务计划：

```json
{
  "sub_tasks": {
    "task_1": {"content": "...", "agent": "SearcherAgent"},
    "task_2": {"content": "...", "agent": "PlannerAgent"},
    "task_3": {"content": "...", "agent": "ItemRetrievalAgent"},
    "task_N": {"content": "...", "agent": "InteractorAgent"}
  }
}
```

规则：
- `InteractorAgent` 或 `PlannerAgent` 必须是最后一个子任务
- `PlannerAgent` 触发重规划（update_plan），继续追加新子任务

### Executor Agents

| Agent | 职责 |
|-------|------|
| `SearcherAgent` | 检索领域知识（原：Google Search；patch：BM25 on knowledge1.csv） |
| `ItemRetrievalAgent` | 从物品库检索候选（原：BGE-M3 embedding；patch：BM25Okapi）|
| `InteractorAgent` | 汇总 memory 中所有检索结果，生成推荐 JSON |
| `InterpreterAgent` | 将上一步 output 转化为下一步 agent 的输入 prompt |

---

## 6. Thought Pattern Distillation (TPD)

- 存储路径：`storage/thought_patterns/`（JSON 文件）
- 内容：每个 pattern 包含 `task_description`、`solution_description`、`thought_template`
- 使用时机：Phase 1，从存储中找最近似 pattern 作为 planning 的 few-shot 引导
- 学习时机：`ENABLE_LEARNING=true` 时，成功的执行轨迹会被 PatternDistiller 提炼为新 pattern
- **复现配置**：`ENABLE_LEARNING=false`（仅使用预存 pattern，不更新）

---

## 7. 用户模拟器（user_simulate/evaluate_agent.py）

TAIRA 不做实时人机交互——用户意图由 `query_data1.csv` 中的 `new_query` 和 `targets` 字段预设。

用户模拟逻辑：
1. `EvaluateAgent.evaluate_valid()`：LLM 判断多个推荐子列表是否有效
2. `EvaluateAgent.evaluate_one_recommend()`：对每个有效子列表，LLM 对推荐的 10 个物品打分（0/0.5/1.0）
3. 计算 `hit_rate`（Recall@10）、`mrr`（MRR@10）、`ndcg`（NDCG@10）

**成功定义**：`hit_rate > 0`（至少一个目标物品出现在推荐列表中）。当 `hit_rate == 0` 时 `fail_flag = True`。

---

## 8. 评估指标

| 指标 | 计算方式 | 说明 |
|------|----------|------|
| `hit_rate` | `# target items found in top-10` / `# total targets` | Recall@10 |
| `mrr` | 第一个找到的目标在列表中的倒数排名 | MRR@10 |
| `ndcgs` | 标准 NDCG@10，relevance score ∈ {0, 0.5, 1.0} | NDCG@10 |
| `fail` | `1 if hit_rate == 0 else 0` | 失败率（等价于 1 - SR）|
| `SR` | `1 - fail.mean()` | Success Rate（主表指标）|

---

## 9. system_config.yaml 配置项

| 配置项 | 含义 | 复现值 |
|--------|------|--------|
| `QUERY_NUMBER` | 从 CSV 取前 N 条 query（后再按 classification==1 过滤） | 500 |
| `TOPN_ITEMS` | 第一阶段 BM25 检索候选数 | 500 |
| `TOPK_ITEMS` | 每次 ItemRetrievalAgent 返回的 top-k | 10 |
| `DOMAIN` | 数据域 | `amazon_music` |
| `MODEL` | LLM 模型名称 | `deepseek-chat` |
| `METHOD` | 方法名（影响 TPD 开关） | `TAIRA` |
| `OPENAI_BASE_URL` | LLM API endpoint | `https://api.deepseek.com/v1` |
| `OPENAI_API_KEY` | LLM API key | （配置文件中，生产环境应用 env var）|
| `GOOGLE_API_KEY` | Google Search API key | `""` 不使用 |
| `GOOGLE_CSE_ID` | Google CSE ID | `""` 不使用 |
| `ENABLE_LEARNING` | TPD 学习开关 | `false` |

---

## 10. QUERY_NUMBER / TOPN / TOPK 的影响

- `amazon_music` 数据集中 `classification==1` 的 query 数约为 **69 条**（500 条总量中）
- `TOPN_ITEMS=500` → BM25 先检索 500 候选，再重排到 TOPK=10
- 增大 TOPN 理论上提升召回但增加处理时间；TOPK=10 与 InterRec 对齐

---

## 11. 随机种子控制

官方 `main.py` **不支持 seed 参数**。随机性来源：
- DeepSeek API 的 temperature（`top_p=0.1`，近似贪婪但非完全确定性）
- Python hash seed

控制方式（本复现）：
- `PYTHONHASHSEED=0/1/2` 作为 seed 0/1/2
- LLM API 随机性无法完全消除（temp=0 仅部分 deterministic）

---

## 12. 复现中遇到的问题（已修复的 patches）

### Patch 1：BGE-M3 密集检索 → BM25

**原因**：BGE-M3 模型未本地缓存，HuggingFace 网络访问受限  
**影响**：物品检索质量可能下降（BM25 < 密集检索），主表需注明  
**修复位置**：`agents/item_retrieval_agent.py`

### Patch 2：Google Search API → BM25 on knowledge1.csv

**原因**：Google Custom Search API 不可用  
**影响**：搜索知识范围限于预存 CSV 文件，覆盖范围可能不足  
**修复位置**：`agents/searcher_agent.py`

### Patch 3：NLTK punkt tokenizer → regex tokenizer

**原因**：NLTK punkt 数据包无法在离线环境下载  
**影响**：分词差异极小（主要是标点处理），预计影响可忽略  
**修复位置**：`agents/item_retrieval_agent.py`（`_tokenize` 函数）

### Patch 4：base Agent `__init__` memory 参数修复

**原因**：`InterpreterAgent` 调用 `super().__init__()` 缺少 memory 参数  
**修复位置**：`agents/base_agent.py`

### Patch 5：LLM 模型 hardcode 修复

**原因**：`parse_user_input` 中 hardcode `llm='gpt-4o-mini'`  
**修复**：改为使用 config 中的 `MODEL`  
**修复位置**：`agents/item_retrieval_agent.py`

### Patch 6：PlannerAgent 出现在非末位子任务中（**关键修复**）

**原因**：DeepSeek LLM 有时违反"PlannerAgent 必须是最后一个子任务"的约束，将其放在中间位置（如 task_2/task_6），导致 `manager_core.py` 中 `self.agents.get("PlannerAgent")` 返回 None → 直接 return (0,0,0,True)  
**影响（未修复）**：~55% 的 query 失败（37/69 queries）  
**修复**：在 `_execute_hierarchical_plan` 非末位循环中检测 `PlannerAgent`，将其作为 no-op 跳过，使流程继续到 `InteractorAgent`  
**修复位置**：`core/manager_core.py`

### Patch 7：ItemRetrievalAgent 返回 DataFrame 行号作为物品 ID（**关键修复**）

**原因**：`execute_task` 返回的 DataFrame 在 `str()` 转换时包含 pandas 行索引（数字如 `173827`），LLM 误将行号当作物品 ID 填入推荐 JSON。`evaluate_agent.py` 用这些数字 ID 在 `metadata.csv` 中做 ASIN lookup 失败，导致评估列表为空  
**影响（未修复）**：多数评估结果为 0（评估器认为推荐列表为空）  
**修复**：`reset_index(drop=True)` + 将 `product_id` 列重命名为 `id`（与推荐 JSON 格式匹配）  
**修复位置**：`agents/item_retrieval_agent.py`
