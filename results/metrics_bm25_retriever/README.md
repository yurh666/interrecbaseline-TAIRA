# BM25 检索器实验指标存档（非主表）

本目录下的 `run_*_seed*.json` 与 `taira_results_bm25.csv` 来自 **ItemRetrievalAgent 使用 BM25** 的实验配置。

- **主表 / 与 InterRec 公平对比**：代码已切换为 **BAAI/bge-m3 + BAAI/bge-reranker-base**；新结果请写入仓库根目录 **`results/metrics/`**。  
- **请勿**将本目录下的数字与 BGE 运行结果直接混为一谈；论文中若引用，须明确标注 **retriever = BM25**。

生成方式（历史）：`PYTHONHASHSEED=0/1/2`，每域 500 queries，`parse_taira_metrics.py` 汇总。
