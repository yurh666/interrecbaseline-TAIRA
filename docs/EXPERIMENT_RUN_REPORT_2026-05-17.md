# TAIRA × InterRec 主实验运行报告（推理 / API 阶段）

**基线**：TAIRA（InterRec 四域对齐数据）  
**指标**：与 `scripts/parse_taira_metrics.py` 一致——主表为 **SR / HR@10 / MRR@10 / NDCG@10 / fail_rate**，并导出 **direct_***（strict item-id）及 `main_table_interrec_paradigm` 等字段写入 `results/metrics/run_<domain>_seed<n>.json`。  
**对比对象**：与仓库内 InterRec 基线文档及既有表对齐时，以同域、同 `QUERY_NUMBER`、同种子协议为准（见下方配置）。

---

## 1. 本机环境（2026-05-17，主实验机）

| 项 | 值 |
|----|-----|
| OS / Kernel | `Linux 5.14.0-570.33.2.el9_6.x86_64`（RHEL 系 el9） |
| GPU | **NVIDIA GeForce GTX 1650**，驱动 **580.65.06**，显存 **4096 MiB**（`nvidia-smi`）；本阶段 **未启用 BGE 在线检索**，`ITEM_RETRIEVAL_RANKING_BACKEND: bm25`，故主路径不依赖 GPU。 |
| Python | **3.10.20**（`~/miniconda3/envs/taira`） |
| PyTorch | **2.5.1+cu124**，`torch.cuda.is_available()` **True**（环境内已装 CUDA wheel，与本次 BM25 推理无强依赖） |
| LLM API | **DeepSeek**，OpenAI 兼用客户端：`OPENAI_BASE_URL=https://api.deepseek.com/v1`，`MODEL=deepseek-chat`（见 `TAIRA/system_config.yaml`） |

依赖安装：`pip install -r TAIRA/requirements.txt`（在 conda env `taira` 中）。`pip freeze` 片段见会话采集（前若干行含 `FlagEmbedding==1.3.4`、`openai==1.64.0` 等）。

---

## 2. 数据与 BGE 产物自检

| 域 | `project_embeddings.npy`（本机 `ls -lh`） | 说明 |
|----|---------------------------------------------|------|
| lastfm | ~11M | 已从 Git LFS 拉取为真实二进制（此前若为 ~133B 则为指针） |
| movielens | ~13M | 同上 |
| amazon_book | ~32M | 同上 |
| yelp | ~226M | 同上 |

**Manifest**：各域 `TAIRA/data/<domain>/bge_embedding_manifest.json` 中 **`model`: `BAAI/bge-m3`**，**`embedding_dim`: 1024**；离线阶段详细证据链见仓库 **`docs/BGE_EMBEDDING_EXPERIMENT_REPORT.md`**（含上游 AutoDL 机上的 GPU 记录与 SHA256 表）。

**检索后端（本跑）**：`TAIRA/system_config.yaml` 中 **`ITEM_RETRIEVAL_RANKING_BACKEND: "bm25"`**，**`BM25_FALLBACK_TO_BGE: false`**——推理侧物品检索为 **BM25（CPU）**，不加载 BGE-M3 / reranker；与「仅 embedding 阶段用 BGE」一致。

---

## 3. 复现命令（从克隆到本阶段）

```bash
# Git LFS（本机无 root 时可用 release 二进制装到 ~/.local/bin ，再在仓库内 git lfs pull）
git lfs install && git clone https://github.com/yurh666/interrecbaseline-TAIRA.git
cd interrecbaseline-TAIRA && git lfs pull

# Conda 环境（示例）
source ~/miniconda3/etc/profile.d/conda.sh
conda activate taira   # Python 3.10+
pip install -r TAIRA/requirements.txt
```

**API 配置（勿提交密钥）**：在仓库根目录创建 **`.env.local`**（已加入 `.gitignore`），内容示例：

```bash
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_API_KEY=<你的 DeepSeek Key，勿入 git>
```

串行脚本会自动 `source` 该文件（见 `scripts/run_serial_interrec_experiments.sh`）。

**四域 × 每域 3 seed（lastfm → yelp → movielens → amazon_book）**，在 **screen** 中Detached 跑（SSH 断开可恢复）：

```bash
cd /path/to/interrecbaseline-TAIRA
screen -dmS taira_interrec bash -lc '
  cd /path/to/interrecbaseline-TAIRA &&
  source ~/miniconda3/etc/profile.d/conda.sh && conda activate taira &&
  export TAIRA_PYTHON="$(command -v python)" &&
  export RUN_LOG="results/serial_run_$(date +%Y%m%d_%H%M%S).log" &&
  exec bash scripts/run_serial_interrec_experiments.sh
'
screen -ls                    # 应看到 taira_interrec (Detached)
tail -f results/serial_run_*.log
# 附着会话：screen -r taira_interrec
```

> **注意**：本机未安装 `tmux`，已用 **`screen -S taira_interrec`** 等价满足「Detach 长跑」要求。请勿 `screen -X quit` 他人会话；仅管理自己的 `taira_interrec`。

---

## 4. 本次启动记录（2026-05-17）

| 项 | 值 |
|----|-----|
| 启动时间（日志首行） | `2026-05-17T16:07:38+08:00`（以 `results/serial_run_20260517_160738.log` 为准） |
| Screen 会话名 | **`taira_interrec`** |
| 主日志 | **`results/serial_run_20260517_160738.log`**（`tee` 全量终端输出） |
| 单域 stdout | `results/<domain>_seed<n>_stdout.log`（各子脚本 `tee`） |
|每 query 日志 | `TAIRA/data/<domain>/logs/TAIRA-*/log_*.log`（若 `system_config` 未改） |
| `QUERY_NUMBER` | **500**（`TAIRA/system_config.yaml`） |
| 随机性 | `PYTHONHASHSEED=0/1/2`  per seed；LastFM 与另三域脚本一致 |

---

## 5. 结果汇总（跑完后填写 / 自动汇总）

实验结束后脚本会执行：

1. `python scripts/collect_taira_results.py` → **`results/taira_results.csv`**
2. `python scripts/write_experiment_summary.py` → **`results/EXPERIMENT_SUMMARY.md`**

**当前状态**：主任务已在后台 **screen `taira_interrec`** 中运行；指标表请在 **`taira_results.csv` 生成后** 打开，或将 CSV 转为论文用表。若某 seed 失败，日志在对应 `results/*_stdout.log` 与 `serial_run_*.log`。

### 5.1 预留结果表（从 `taira_results.csv` 复制）

| dataset | seed | SR | HR@10 | NDCG@10 | fail_rate | 备注 |
|---------|-----:|---:|------:|--------:|----------:|------|
| （待 CSV） | | | | | | |

---

## 6. 后续工作（对照原始 prompt 清单）

- [x] 四域 embedding 文件体积累计合理、LFS 已拉取  
- [x] 串行 **4 × 3 seed**（脚本已改为 LastFM 也跑 0–2）  
- [x] API 使用 DeepSeek，`system_config` 与 env 一致  
- [x] 长任务在 **screen** detach  
- [ ] 跑完后核对 **`results/taira_results.csv`** 与论文 `QUERY_NUMBER`/模型名一致  
- [ ] `git status`：勿提交 `.env.local`、勿提交含 API Key 的日志  

---

## 7. 安全说明

**不得**将 **API Key** 写入可追踪文件或提交到 Git。本机使用仓库根目录 **`.env.local`**（已 `.gitignore`）。若 Key 曾在聊天中暴露，建议在 DeepSeek 控制台**轮换密钥**。

---

## 8. 参考文档

- 离线 BGE：`docs/BGE_EMBEDDING_EXPERIMENT_REPORT.md`
- 串行入口：`scripts/run_serial_interrec_experiments.sh`
- 单域：`scripts/run_taira_interrec_dataset.sh`、`scripts/run_lastfm_seeds.sh`
