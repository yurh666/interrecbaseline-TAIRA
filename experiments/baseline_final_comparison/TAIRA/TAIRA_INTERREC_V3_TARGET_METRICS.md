> **【已并入主报告】** 目标线全文见 **`TAIRA_FINAL_REPORT.md`** §8。

# InterRec / v3 — 相对 TAIRA 的目标线（自动生成草案）

下列 **TAIRA 参考值**取自 `results/EXPERIMENT_SUMMARY.md`（三 seed mean）。**括号**中为 **脚注语义**：主质量列使用 **HR@10/NDCG@10/MRR@10（LLM 评估列）**，而 **管线 SR**=`1-fail_rate`。

**preference_error：** **cannot set numeric target yet** — 未发现该指标。补齐：在 evaluator 中加用户偏好向量距离或分类误差导出。

## A. Minimum acceptable target（不达标则不建议把 TAIRA 放主对比表）

对每个 **已对齐数据集** \(D\)：令 \(b\) 为 TAIRA 的 **HR@10**（作为单轮 Hit 代理），\(n\) 为 **NDCG@10**，\(m\) 为 **MRR@10**。

1. **SR@10（若采用桥接定义 `SR@10 := HR@10`）**：InterRec/v3 **不得低于** \(b - 0.02\)（相对容差可随域噪音调整；Yelp 域应使用 **同一 fail 处理规则** 再比）。  
2. **NDCG@10**：不低于 \(n - 0.03\)。  
3. **MRR@10**：相对下降 **不超过 8%**（即 \(\ge 0.92\,m\)）或绝对下降 ≤0.05，取松者。  
4. **交互**：若比较 `avg_ask_count`，InterRec **允许 >0**（因其有提问）；应同时报 **成功所需轮数** 证明效率。  
5. **成本**：**当前 baseline 无 token / wall time 记录** ⇒ **cannot set numeric target yet**；若未来 TAIRA 账本补齐，再设 **≤1.5× tokens** 或明确压缩方案。

## B. Paper-ready target

1. 在 **同一 setting**（配对的 session 列表 + 同一评估列）下：  
   - **`SR@10`（桥接）或 NDCG@10** 至少一项 **统计上优于** TAIRA mean（建议 **单尾 paired bootstrap**；非仅 n=3 偶然）。  
2. **MRR@10** 不满足 A(3) 的下限则 **只能作补充材料**。  
3. **fallback / malformed**（JSON 解析失败率）**应显著低于** TAIRA 在难域表现或与其同量级并解释原因。  
4. **非小样本偶然**：需 **≥3 seeds** 或更大样本 + 置信区间。

## C. Strong target

1. **HR@10 / NDCG@10 / MRR@10** 中 **至少两项** 同时优于 TAIRA mean。  
2. **成本**：若可测，**Total tokens ≤ 1.5× TAIRA** 或给出 **>20% 下降** 的蒸馏/缓存方案。  
3. **稳定性**：跨 seed 方差 **不显著高于** TAIRA（同向指标）。

## D. Efficiency target

若 **质量在 A 的容差内持平**：  
- **LLM HTTP / tokens / wall time** 至少 **下降 20%**；**或**  
- **平均成功轮数**（仅 InterRec 可定义）**显著低于** 多轮基线（TAIRA 无对应量，需另设 multi-turn baseline）。

---

## 附：TAIRA 参考均值速查（LLM 列）

| dataset | HR@10 | NDCG@10 | MRR@10 | fail_rate (≈1-SR_pipeline) |
|---------|-------|---------|--------|----------------------------|
| amazon_book | 0.6739 | 0.8366 | 0.9088 | ~0.090 |
| lastfm | 0.7224 | 0.8705 | 0.9214 | ~0.077 |
| movielens | 0.4774 | 0.6117 | 0.7024 | ~0.280 |
| yelp | 0.2956 | 0.3661 | 0.4202 | ~0.566 |

（更细 per-seed 见 `TAIRA_metric_table.csv`。）
