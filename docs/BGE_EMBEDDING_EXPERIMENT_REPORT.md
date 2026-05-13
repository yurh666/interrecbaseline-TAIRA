# BGE-M3 物品向量化离线实验说明与中间结果报告

本文档说明 [interrecbaseline-TAIRA](https://github.com/yurh666/interrecbaseline-TAIRA) 在 InterRec 四数据集上，使用 **BAAI/bge-m3** 生成物品稠密向量（`project_embeddings.npy`）的实验目标、环境与可复现证据链，并列出后续步骤。

---

## 1. 实验目标与要求

| 项目 | 内容 |
|------|------|
| 任务 | 对每个推荐域内的全部物品，将 `project_info` 文本编码为 **1024 维** L2 归一化 float32 向量，供后续检索或对齐基线使用。 |
| 模型 | **BGE-M3**（Hugging Face Hub ID：`BAAI/bge-m3`），通过 `FlagEmbedding.BGEM3FlagModel` 取 **`dense_vecs`**。 |
| 数据集（InterRec） | `lastfm`，`yelp`，`movielens`，`amazon_book`（与 `scripts/precompute_bge_embeddings.py` 中 `INTERREC_DOMAINS` 一致）。 |
| 设备（当前仓库约定） | 离线预计算 **默认要求 CUDA**；调试可加 `--allow-cpu`（不推荐正式实验）。 |
| 产物 | 每域：`project_embeddings.npy`（形状 `(N, 1024)`）、`bge_embedding_manifest.json`（元数据）。默认可置于 `TAIRA_EMBEDDINGS_ROOT/<domain>/` 或推库时与代码一同放在 `TAIRA/data/<domain>/`（本报告对应 SHA256 见第 4 节）。 |

---

## 2. 环境与超参（本机记录，2026-05-13）

以下在容器 **`autodl-container-4m2rp8n07l-a6209b1d`** 上采集（AutoDL 类环境）。

| 类别 | 值 |
|------|-----|
| OS / Kernel | Ubuntu 系，`Linux 5.15.0-78-generic`，`x86_64` |
| GPU | **NVIDIA GeForce RTX 4080 SUPER**（`nvidia-smi` 报告 Driver **580.105.08**，CUDA **13.0** 为驱动 API 版本） |
| Python | **3.10.8**（Miniconda/venv） |
| PyTorch | **2.5.1+cu124**（CUDA 12.4 构建的 wheel）；`torch.cuda.is_available()` **True** |
| 预计算脚本 | `scripts/precompute_bge_embeddings.py` |
| 批大小 | 离线跑四域时 **`--batch-size 64`**（与 tmux/ bundle 脚本一致） |
| 权重来源（成功跑通的一次） | 本地 Hub 缓存快照：`.../huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181`（revision 与官方 **bge-m3** 一致） |
| 推理侧配置（当前 `system_config.yaml`） | `ITEM_RETRIEVAL_RANKING_BACKEND: "bm25"`：在线物品检索走 **BM25（CPU）**；BGE 仅用于 **离线** 向量化（与「仅 embedding 构建用 BGE」的设计一致）。 |

环境变量常用组合（大文件放数据盘示例）：

- `AUTODL_ARTIFACTS_ROOT=/root/autodl-tmp/interrecbaseline-TAIRA`
- `TAIRA_EMBEDDINGS_ROOT=$AUTODL_ARTIFACTS_ROOT/embeddings`
- `HF_HOME=$AUTODL_ARTIFACTS_ROOT/huggingface`
- `BGE_M3_LOCAL_DIR=$AUTODL_ARTIFACTS_ROOT/models/BAAI-bge-m3`（下载目标目录，需 `config.json` 齐全后再 `--model` 指向该路径可避免误触 Hub）

---

## 3. 「是否使用 GPU 做 embedding」— 证明边界与可复现证据

### 3.1 能严格说明什么、不能说明什么

- **能严格说明的（可重复实验）**  
  在同一台机器、当前软硬件下执行 `scripts/verify_bge_embedding_gpu_evidence.py` 时，可以观测到：
  - `torch.cuda.is_available() == True`；
  - 首次 `encode` 之后，`BGEM3FlagModel` 的 **首个参数位于 `cuda:0`**；
  - **CUDA 显存分配**在首次 `encode` 后增加约 **1.1×10⁹ bytes**（Lazy 将权重/激活搬到 GPU 的典型表现）；
  - 与磁盘上 `project_embeddings.npy` **第 0 行**（对应元数据中第一条 `project_info`）的 **余弦相似度 ≈ 0.9999987**，证明向量与 **同一 BGE-M3 前向、同一归一化流程** 一致。

  完整命令输出已保存为：`docs/bge_gpu_verification_run.txt`（与本报告同期提交）。

- **不能对「2026-05-13 历史那一次进程」做法庭级单独证明的点**  
  当时 `precompute_bge.log` 中 **未记录** `cuda=…` 或 `nvidia-smi` 采样，因此无法仅凭该日志对「那一个 PID 是否全程未落 CPU」做无损追溯。  
  同时，**算法层面**可确认：唯一编码路径为 `BGEM3FlagModel.encode` → `dense_vecs`，权重为 **BAAI/bge-m3** 快照；在 **CUDA 可用且未传 `--allow-cpu`** 时，当前脚本会拒绝无 GPU 的预计算，与「正式 embedding 在 GPU 上完成」的工程要求一致。

### 3.2 结论表述建议（论文/报告用语）

推荐写法：  
「离线向量化使用 **FlagEmbedding 的 BGE-M3 稠密向量**；在配备 CUDA 的环境中，我们通过显式验证脚本确认 **模型参数驻留于 GPU 且前向后 GPU 显存显著增长**，并与已落盘的 `project_embeddings.npy` 在样本级数值上一致。」  
若需更强审计，可在今后每次批量预计算时额外将 `nvidia-smi` 或 PyTorch `memory_allocated` 摘要 **追加写入** `precompute_bge.log`（可在 `precompute_bge_embeddings.py` 中打一行即可）。

---

## 4. 中间结果清单（四域）与校验

以下 SHA256 针对 **当前纳入版本库路径** `TAIRA/data/<domain>/` 下的文件（与 `AUTODL_ARTIFACTS_ROOT/embeddings` 曾为同一次生成结果拷贝）。

| domain | `n_items` × dim | `project_embeddings.npy` SHA256 | `bge_embedding_manifest.json` SHA256 |
|--------|-----------------|---------------------------------|----------------------------------------|
| lastfm | 2665 × 1024 | `a02950a78ab5da185e5d809aa4f8bd0075fbfe41764f02b5df69bde324b8e2f3` | `a390cfe66091636e23dd8b968274944f96415c528057d12639ba1e843c754dea` |
| yelp | 57675 × 1024 | `173ed8f5c2493a288b7fae9824e46f5a025987ce13deaf163369a97779bda311` | `36dfa7fdcf367586720d27b19ab6562276700d251e257d47b8f36e87e98c5804` |
| movielens | 3115 × 1024 | `f7752a02a77af08f74ee3ee5e589f64be1959f975824768ec0d782ae1a45bf5d` | `37738a4072c29b43bac607f56c7a20a17ce506c710df81d5b69187dedd2930b7` |
| amazon_book | 7992 × 1024 | `5cc549ed840205f204996ada4ef793bcd06cb41e1cd150b5e297524b7bb7d0b3` | `d0c239d633cd5aee8592e57a0c50b8b233bc67cf62b6d8e77e31da291cbfcf5f` |

Manifest 中 **`model` 字段统一为 `BAAI/bge-m3`**（与论文/表格 Hub ID 对齐），`embedding_dim: 1024`，`l2_normalized_rows: true`。

**Git LFS**：`.gitattributes` 已对 `TAIRA/data/**/project_embeddings.npy` 配置 `filter=lfs`；克隆后需执行 `git lfs install` 与 `git lfs pull`。

---

## 5. 复现命令摘要

```bash
cd /path/to/interrecbaseline-TAIRA
python3 -m venv .venv && source .venv/bin/activate
pip install -r TAIRA/requirements.txt

# 推荐：一次性 GPU 离线阶段（含下载目录与四域预计算，需网络以下载权重时）
bash scripts/bge_offline_gpu_bundle.sh

# GPU 与数值一致性证据（lastfm 示例）
python scripts/verify_bge_embedding_gpu_evidence.py --domain lastfm
```

推理/主实验（非 GPU 向量化）：按 `TAIRA/system_config.yaml` 与 `scripts/run_taira_after_bge_embeddings.sh` 等继续（需配置 LLM API Key）。

---

## 6. 后续工作建议

1. **主实验流水线**：为各域设置 `DOMAIN`，配置 `OPENAI_API_KEY` / `OPENAI_BASE_URL`，运行 TAIRA 主入口（参见 `scripts/run_taira_hybrid_main.sh` 或项目文档）。  
2. **可选基线对比**：若需在线 **BGE 稠密 + rerank**，将 `ITEM_RETRIEVAL_RANKING_BACKEND` 改为 `bge` 并确保本机可加载 `BGE_RERANKER_MODEL`。  
3. **日志增强（可选）**：在 `precompute_bge_embeddings.py` 每个 domain 开始时打印 `torch.cuda.get_device_name(0)` 与 `torch.cuda.memory_allocated()`，便于论文附录直接引用。  
4. **网络不可达时**：优先保证 `BGE_M3_LOCAL_DIR`（或 Hub cache snapshot）已有完整权重，再 `--model` 指向本地目录；避免在离线环境触发 `snapshot_download`。

---

## 7. 参考仓库

- 上游公开仓库：<https://github.com/yurh666/interrecbaseline-TAIRA>  

（本报告与中间结果向量、验证脚本随该仓库分支 **`main`** 一并维护。）
