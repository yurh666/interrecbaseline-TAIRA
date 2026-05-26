# Paper-Readiness — InterRec/v3 「相对 MCMIPL」输赢判定草稿

字段：`paper_ready_against_this_baseline`

| 取值 | 条件（AND） |
|------|--------------|
| `not_ready` | **任一**：(a) Yelp 域 baseline 未完；(b) SR/HR 定义混搭；(c) 无统一 candidate/manifest evidence。→ **现状默认落此档。** |
| `weak_ready` | 完成三域对齐跑 + evaluator 脚注齐全 + 单次 seed 显著提升但方差未知。 |
| `ready` | 三 domain × 三 seed；(质量或交互) ⩾一项 **honest improvement**（同定义）；成本故事自洽。 |
| `strong_ready` | 「ready」基础上：多维度领先 + malformed/fallback ablation done。 |

**「不可以算赢」清单（复述 prompt）：**

- setting 漂移 / 仅用 n=5 micro-run。  
- 只赢 CRS-SR10 但 **HR/NDCG/MRR(LLM)** 断崖（若该类指标为论文主轴）。  
- InterRec tokens **>10×** 且无 compression story。  

---

**当前：`not_ready`** —— MCMIPL **Yelp 未完成**，且评测协议 ≠ TAIRA triple 默认列。
