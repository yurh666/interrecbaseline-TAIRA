# GPU 阶段操作说明（给执行者 / Agent 的 Prompt）

将本文件整段作为任务说明粘贴到 **有 NVIDIA GPU、可访问 HuggingFace / 模型下载** 的环境（Cursor / 终端均可）。

目标仓库：[yurh666/interrecbaseline-TAIRA](https://github.com/yurh666/interrecbaseline-TAIRA)

---

## 任务目标

1. **拉取代码并检查结构**  
   - `git clone https://github.com/yurh666/interrecbaseline-TAIRA.git && cd interrecbaseline-TAIRA`  
   - 确认存在：`TAIRA/agents/item_retrieval_agent.py`（BGE 检索分支）、`scripts/precompute_bge_embeddings.py`、`scripts/bge_offline_quick_test.py`、`scripts/gpu_bge_offline_phase.sh`。  
   - 确认数据：`TAIRA/data/{lastfm,yelp,movielens,amazon_book}/metadata.csv`。

2. **配置 Python 环境**  
   - 建议：`python3 -m venv .venv && source .venv/bin/activate`  
   - `pip install -U pip && pip install -r TAIRA/requirements.txt`  
   - 验证 GPU：`python3 -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"` 应为 `True` 与非空设备名。

3. **快速自检（Quick test，不依赖全量 npy 时仅测导入）**  
   - 至少：`python3 -c "from FlagEmbedding import BGEM3FlagModel; print('FlagEmbedding OK')"`  
   - **在某一域已生成 `project_embeddings.npy` 之后** 再跑：  
     `python3 scripts/bge_offline_quick_test.py --domain lastfm`

4. **离线生成 BGE-M3 向量（主交付物）**  
   - 在仓库根目录执行：  
     `python3 scripts/precompute_bge_embeddings.py --all-interrec-domains --batch-size 64`  
     （显存不足时把 `--batch-size` 改为 `16` 或 `32`。）  
   - **每个域**应产出：  
     - `TAIRA/data/<domain>/project_embeddings.npy`  
     - `TAIRA/data/<domain>/bge_embedding_manifest.json`

5. **Git / Git LFS（大文件必做）**  
   - `project_embeddings.npy` 在 **Yelp** 等域可能 **>100MB**；GitHub 单文件限制 100MB，**必须**使用 [Git LFS](https://git-lfs.com/)：  
     ```bash
     git lfs install
     git lfs track 'TAIRA/data/**/project_embeddings.npy'
     git add .gitattributes
     ```  
   - 若 `.gitattributes` 已由上游提交，确认其中含对 `project_embeddings.npy` 的 `filter=lfs` 规则即可。  
   - 添加并提交：  
     ```bash
     git add TAIRA/data/*/project_embeddings.npy TAIRA/data/*/bge_embedding_manifest.json .gitattributes
     git commit -m "data: precompute BGE-M3 item embeddings for InterRec domains"
     git push origin main
     ```  
   - **禁止**将 `OPENAI_API_KEY`、DeepSeek 密钥等写入 `system_config.yaml` 后再 push；密钥仅使用环境变量（见 `TAIRA/utils/task.py`）。

6. **交接给下一阶段（API / CPU 跑主实验）**  
   - 确保远端 `main` 上已能看到各域的 `project_embeddings.npy`（LFS 指针）与 `bge_embedding_manifest.json`。  
   - 在实验机上：`git pull` 后执行 `git lfs pull`（若使用 LFS）。  
   - 再使用 `scripts/run_taira_after_bge_embeddings.sh <domain>` 并设置 `OPENAI_API_KEY`。

---

## 一键脚本（可选）

仓库内：`./scripts/gpu_bge_offline_phase.sh`（在项目根目录执行；仍须人工检查 `git commit` 信息与网络/LFS）。

---

## 常见问题

| 现象 | 处理 |
|------|------|
| HuggingFace 超时 | 配置 `HF_ENDPOINT` 镜像或本机 `huggingface-cli download` 预缓存后离线跑。 |
| 显存 OOM | 减小 `--batch-size`；或逐域 `--domain lastfm` 分开跑。 |
| GitHub 拒绝推送 | 单文件超 100MB 且未走 LFS；执行 `git lfs migrate` 或按上表启用 LFS 后重新添加文件。 |
