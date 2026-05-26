# MCMIPL vs InterRec / v3 — Method Gap（对比要点）

InterRec/v3 **核心范式（来自任务 prompt）：**

- preference **belief**
- Bayesian / Gaussian 更新线索
- VOI **`when-to-ask`**
- hypothesis-level question
- **`frontier_clustered_v32`：belief_scores→Top-K + boundary frontier + cluster contrast 问题**，缓解 entropy-VOI 与 item ranking 不对齐。

**MCMIPL 对齐 / 分叉：**

| 能力 | InterRec/v3 | MCMIPL |
|------|-------------|---------|
| item-level ranking utility | 设计目标的一部分 | CRS success / reward |
| 显式不确定性 belief | 有 | 不显式等价物 |
| 「为何此刻问」可解释性 | VOI / frontier | 策略层偏黑盒 |
| 问题生成 | hypothesis + frontier clustering | 离散属性 MCQ |
| LLM HTTP 成本 | 可能高 | 本轮 **0** |

**结论定位：**

- MCMIPL 更偏 **强 CRS + GNN + RL**，不是 **LLM 信念交互**。  
- InterRec-v3 若写论文：**统一 evaluator 后**再比 `SR/NDCG/MRR`；在 **交互机制与可解释 Ask** 叙事上应占理论优势位。  
- 若硬指标打平：仍可强调 **belief update + frontier contrast** vs **端到端离散策略**。  
- 若在 **定义混用 SR** 情形下「赢」：**无效胜利**——先修协议。
