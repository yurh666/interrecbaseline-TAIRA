> **【已并入主报告】** 见 **`TAIRA_FINAL_REPORT.md`** §9。

# TAIRA — Paper-readiness 判定规则（面向 InterRec / v3）

**`paper_ready_against_this_baseline`（当前占位）：** `not_ready`

> 因工作区内 **尚无**可与 TAIRA **逐会话对齐**的 InterRec / `frontier_clustered_v32` run 摘要（`run_summary.json`/`full_log.jsonl`），**无法在数值上签发** `ready`。**规则以下文为准**，待对齐跑分后重新判定。

---

## 「可宣称战胜 TAIRA」建议条件（宜全部满足再标 `ready`）

1. **同一 dataset**：域、预处理脚本版本、数据源路径可核验。  
2. **同一 test sessions**：会话 id 顺序与 manifest 与 TAIRA 检查点可追溯一致（注意 TAIRA 部分域 **`n_queries` < QUERY_NUMBER**，需先完成对账）。  
3. **同一 candidate / target / evaluation**：Top-K、命中定义（**LLM 判分 vs strict item-id**，二选一作主列并在附录给另一列）。  
4. **SR@10 或 NDCG@10**：在 **双方书面约定的可比定义下**有一项 **统计显著优于** TAIRA mean（推荐 bootstrap / CI，不只报告点估计）。  
5. **MRR@10**：相对 TAIRA **不明显下跌**（容差见 `TAIRA_INTERREC_V3_TARGET_METRICS.md`）。  
6. **avg_ask_count / 成本**：多轮方法的 **发问与 token**须在可接受范围；**TAIRA 侧 token/wall-time 在本仓库中为 not available**，**不得单方面宣称成本占优**——需双方都落盘后再比。  
7. **fallback / malformed**：v3 的解析失败、占位推荐应可控，并在文中披露率。  
8. **质性案例**：至少有案例说明 **v3 的提问/信念更新为何优于「无发问单轮 TAIRA」**。

## 不构成「打赢」的常见情形

| 情形 | 说明 |
|------|------|
| 仅 n≈5 或单 seed 「偶然嬴」 | 稳定性不足 → 最高 `weak_ready` |
| setting 漂移 | Taboo，`not_ready` |
| 只嬴「桥接 SR@10」但 NDCG/MRR 双差 | 「质量叙事」不立 |
| 成本高一个数量级以上且无压缩方案 | 「工程可比性」不立 |
| TAIRA baseline 在本域 **不完整/未对齐 session 列表** | 比较无效 |
| v3 **大量 fallback、无真实 ask-update 闭环** | 不满足上述 8 |

---

## Enum 取值说明

| 取值 | 含义 |
|------|------|
| `not_ready` | 缺对齐跑分、或主指标/协议未闭合。**→ 当前默认。** |
| `weak_ready` | 有苗头但 variance 大、仅单维度略优、caveat 仍多 |
| `ready` | 满足上表必要条件 + fair setting |
| `strong_ready` | 多指标占优 +（若可测）成本受控 + 质性证据 |
