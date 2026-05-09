# Vibe Coding 交接 Prompt（新机：LastFM seed2 + 三数据集）

复制下面整块给另一台服务器的 AI / 助手使用。

---

你是负责在 Linux 上跑实验的工程助手。严格按照以下步骤执行，使用 **bash + tmux**（或 screen），SSH 断开不能杀进程。

## 实验目的

仓库 **interrecbaseline-TAIRA** 是在与 **InterRec 对齐的数据与评测协议** 下运行的 **TAIRA 基线**。  
本项目相对论文的官方实现有约定制：检索多为 **BM25**、LLM 多为 **DeepSeek（OpenAI 兼容 API）**、数据集域与原文 Amazon 不尽相同——结果写论文时需脚注，不要求与原文表格逐格一致。

**本次在你这台机器上要完成：**

1. **LastFM：只跑 `seed=2`**（seed 0 / 1 已在另一台机子跑完，禁止重复覆盖）。
2. **依次再跑三个域**：`yelp`、`movielens`、`amazon_book`；**每个域按脚本内含逻辑跑齐 `PYTHONHASHSEED=0,1,2` 三个 seed（串行）**。
3. 跑完后把 **CSV、`results/metrics/` 里的 JSON、`stdout` 日志** 整理好，做一次 **聚合说明**（均值±std），并 **`git commit` + `git push`** 到远端（需操作者自己有 GitHub 凭据）。

## 1）克隆 / 更新代码

```bash
git clone https://github.com/yurh666/interrecbaseline-TAIRA.git
cd interrecbaseline-TAIRA
git pull origin main   # 确保含 scripts/run_lastfm_seeds.sh 支持「仅跑某些 seed」的更新
```

## 2）环境

- Python：推荐 **conda** 虚拟环境，`pip install -r TAIRA/requirements.txt`。
- **所有长任务必须用与跑 `main.py` 相同的解释器**跑 `parse_taira_metrics.py`（避免系统 `python3` 缺 pandas）。
- 填写 **`TAIRA/system_config.yaml`**：`MODEL`、`OPENAI_BASE_URL`、`OPENAI_API_KEY`、`QUERY_NUMBER`（如 500）、`DOMAIN` 会被脚本改写，勿手改卡住即可。

```bash
cd TAIRA && conda activate <你的env>   # 示例
```

## 3）LastFM — 仅 seed 2（不要跑 0/1）

仓库根目录下：

```bash
cd "$(git rev-parse --show-toplevel)"
tmux new -s taira_lastfm_s2
bash scripts/run_lastfm_seeds.sh 2
# detach：Ctrl-B 再按 d
```

等价环境变量：`TAIRA_LASTFM_SEEDS="2" bash scripts/run_lastfm_seeds.sh`。

**永远不要**在未确认的情况下重复跑 seed 0/1——会 **混淆** `results/` 与 `logs/`。**若必须重跑某 seed**，先备份对应 `result-*.csv` 与 stdout。

### 与老机器的职责切分（重要）

若老机器的 `screen` 里仍是 **旧版** `run_lastfm_seeds.sh`（`for SEED in 0 1 2`），**seed 1 结束后通常会立刻启动 seed 2**。处理方式：

- **推荐**：`screen -r taira_lastfm`，在 **seed 1 完成且已写完 CSV、metrics 刚打印完毕**、`Running seed=2` **尚未开始前**尽快 **`Ctrl+C`**，使 seed 2 **仅在**新机上跑。
- 若 seed 2 **已在老机器误启动**：立刻 **`Ctrl+C`** 停当前 `python main.py`，删掉或移除误生成的 `TAIRA/data/lastfm/logs/TAIRA-*` 半成品目录与空的/错的 `results/lastfm_seed2_stdout.log`，再在新机独占跑 `bash scripts/run_lastfm_seeds.sh 2`。

**说明**：已更新到磁盘上的 `run_lastfm_seeds.sh` **不会**被「正在跑着」的旧 `screen` 进程重新加载；要防止老机自动启 seed 2，仍依赖 **`Ctrl+C` 或对误跑进程的停止**。

## 4）其余三个数据集（每域三个 seed，串行）

仍在仓库根目录，建议 **每个域单独 tmux 顺序执行**：

```bash
tmux new -s taira_yelp
cd "$(git rev-parse --show-toplevel)"
bash scripts/run_taira_interrec_dataset.sh yelp

tmux new -s taira_ml
bash scripts/run_taira_interrec_dataset.sh movielens

tmux new -s taira_book
bash scripts/run_taira_interrec_dataset.sh amazon_book
```

脚本会改写 `DOMAIN`、顺序跑 seed 0→1→2、写 `results/metrics/` 并尝试聚合。

若某域缺 `query_data1.csv`，参阅 `scripts/convert_interrec_to_taira.py`（仓库多数情况下已自带 csv）。

## 5）要不要「所有 seed 并行」？

**默认不要。** 并行启动多个 `main.py` **很少能接近 3× 加速**：瓶颈多为 **API 延迟与限流**（容易 429）；每实例还各建一份 **BM25 索引**，**内存成倍上涨**。不占 GPU ≠ 不占资源。**本任务以串行为准**，除非人工确认额度与内存富余并要求并行。

## 6）监控

- `tmux ls` / `tmux attach -t <session>`
- 进度：`TAIRA/data/<domain>/logs/TAIRA-*/result-*.csv` 与 `results/*_stdout.log`
- 进程：`ps aux | grep 'main\.py'`

## 7）交付与上传

- 汇总 **LastFM seed2** 与 **yelp / movielens / amazon_book** 各 3 seed。指标 **一律只增不减**：除原来的 **`SR`、`HR@10`、`MRR@10`、`NDCG@10`、`fail_rate`、`HR@10_succ`、`direct_*`** 外，解析脚本还会在 JSON 里附带 **`main_table_interrec_paradigm`**（主表 SR@\* / AvgT / hDCG 映射）与 **`protocol_interrec_item_id`**（与 method1 最接近的 ID 命中）。交付说明里建议 **三组都报**，不要只报其中一组。
- 在仓库根目录：

```bash
git add -A
git status
git commit -m "Add LastFM seed2 and yelp/movielens/amazon_book runs"
git push origin main
```

## 指标：读 `results/` 与对照 method1（InterRec）

每条 `result-*.csv` 跑完后必须执行：

```bash
cd "$(git rev-parse --show-toplevel)"
<你的conda python> scripts/parse_taira_metrics.py \
  "TAIRA/data/<dataset>/logs/<某次TAIRA目录>/result-*.csv" \
  "results/metrics/run_<dataset>_seed<SEED>.json" <SEED>
```

生成的 **`run_*_seed*.json`** 中包含：

1. **原生**：`SR`、`HR@10`、`MRR@10`、`NDCG@10`、`fail_rate`（LLM / 任务失败语义，见 `docs/taira_reproduction_report.md` §3.4）。
2. **`main_table_interrec_paradigm`**：与主表「多轮」列对齐用的 **SR@5/10/15（均等于 LLM 的 HR@10）、AvgT=1、hDCG=NDCG@10**；供和 MCMIPL 同列排版，**脚注说明单轮映射**。
3. **`protocol_interrec_item_id`**（若 CSV 有 `direct_*`）：**物品 ID 是否与 `future_test` 在 top-10 相交** —— **与 InterRec（method1）硬协议最接近**，写论文时 **TAIRA vs ours 应用这一路作核心对照**。

汇总多 seed 时：`python scripts/collect_taira_results.py` 会刷新上级 `comparison/results/taira_results.csv`（若存在 `comparison/` 目录）；并打印各指标 mean±std。**交付报告里请同时贴：原生 + 主表映射 + ID 协议三路摘要。**

---

## 附录：将来在本机只想跑到 seed 1

```bash
TAIRA_LASTFM_SEEDS="0 1" bash scripts/run_lastfm_seeds.sh
```

（需使用支持该变量的 `run_lastfm_seeds.sh` 版本。）
