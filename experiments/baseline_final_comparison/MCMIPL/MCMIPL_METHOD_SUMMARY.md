# MCMIPL — Method Summary（中文）

1. **方法目标：** 在多轮会话推荐场景中，通过学习 **多条兴趣路径**（multi-interest），在每一步从 **结构化多选题属性**中获取用户反馈并推荐物品，提高 **会话内命中率**。
2. **核心机制：** 图神经网络编码 **users/items/attributes**，结合 **replay buffer** 的策略梯度式训练（WWW’22 原版实现），以 **离散动作（属性选择→推荐候选）** 驱动对话展开。
3. **用户偏好如何建模：** 通过 **图谱嵌入（TransE 预训练 + GCN 表征）与交互轨迹**刻画；不显式维持概率化的「belief Gaussian」一类对象。
4. **是否主动提问：** **是**：每轮可对用户发出 **预设属性选择题**。
5. **问题如何生成：** 源自 **离散属性词典 + 策略输出的 attribute option**（与 LLM hypothesis 问答不同）。
6. **用户回答如何更新状态：** 通过环境与 buffer 驱动的 **隐含状态嵌入更新**（不显式可读自然语言）。
7. **最终如何排序 item：** 策略在 **embedding 空间**上对候选条目打分／筛选（实现细节在原论文与该仓库）。
8. **是否依赖 LLM：** **本轮 CPU Phase B：** **否**。
9. **是否依赖 RL：** **是**（核心）。
10. **主要优势：** 经典 CRS+RKG+RL baseline；可复现有公开论文；在多属性反馈结构下较强。
11. **主要短板：** 与现代化「LLM+BM25 hybrid」或 Bayesian belief+V3 `frontier_clustered_v32` 机制 **不在同一解法族**。
12. **与 InterRec / v3 最大差异：** InterRec/V3：**显式信念 + VOI/`frontier_clustered` 对齐 question–ranking**。MCMIPL：**端到端离散策略 + 图谱嵌入**，无同一「belief-hypothesis-frontier」解释链。
