> **【已并入主报告】** 见 **`TAIRA_FINAL_REPORT.md`** §6。

# TAIRA — 方法思路摘要（中文）

1. **方法目标**  
   在给定用户观测历史的前提下，经由 **大型语言模型驱动的多智能体协作**完成 **一次性（单轮）** 的物品检索与推荐，使候选 **Top-K**（本仓库中为 10）尽量覆盖用户潜在的下一交互目标（对齐 InterRec pipeline 时需与 `future_test` 对上）。

2. **核心机制**  
   Planner / Searcher / ItemRetrieval / Interactor 等角色分工：**规划 → BM25（在线）相关知识与物品检索 → 生成最终列表**，整体为 **单次 forward session**。

3. **用户偏好建模**  
   **无显式概率信念或embedding 后验**；偏好信息主要以 **LLM context 推断 + BM25 匹配**隐含表达。

4. **是否主动提问**  
   **否**——无面向真实/simulator 用户的多轮 **偏好澄清提问**闭环（与用户规则型 CRS 有别）。

5. **问题如何生成**  
   不适用 CRS 语义；内部子任务可被 LLM 分解为检索 query，但并非用户可读的多选题式 preference elicitation。

6. **用户回答如何更新状态**  
   **无**：无用户应答驱动下的 **belief update**。

7. **最终如何排序 item**  
   通过检索链得到的候选并经 LLMInteractor 结构化输出固定长度列表；本项目在线路径配置为 **`ITEM_RETRIEVAL_RANKING_BACKEND: bm25`**。

8. **是否依赖 LLM**  
   **强依赖**——规划与生成环节核心均由外部 LLM 完成（仓库配置示例为 `deepseek-chat`）。

9. **是否依赖强化学习 / policy**  
   `ENABLE_LEARNING: false`；主线 **未见 RL policy**训练环节。

10. **主要优势**  
    开箱即用的 **端到端语言能力**；在 **词汇检索**可用的域上可同时给出 **语义解释链**相关的中间文本（若记录日志）。

11. **主要短板**  
    - **不稳定输出**导致解析失败 (`JSONDecodeError` 历史日志)。  
    - **高 fail_rate 域（Yelp）**显示跨域迁移脆弱。  
    - **与用户交互范式不对齐 CRS 基准**时需大量脚注。

12. **和 InterRec / `frontier_clustered_v32` 的最大差异**  
    InterRec/v3：**显式信念 + 结构化提问 + VOI/边界簇问题**。TAIRA：**单轮 Agentic RAG**，**不显式建模不确定性**，**不进行假设级 Bayesian 更新**。
