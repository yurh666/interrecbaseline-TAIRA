"""Checkpoint-aware TAIRA runner.

Drop-in replacement for main.py that supports resuming interrupted runs.
Each finished query is appended to the checkpoint CSV immediately.

Usage:
  python main_resume.py                                      # fresh run (timestamped dir, same as legacy main_resume)
  python main_resume.py --resume-csv <path>                  # if path exists: skip done ids and append;
                                                             # if path missing: create parent dirs and write there (stable checkpoint)

Stable checkpoint layout (recommended from shell):
  results/checkpoints/<domain>/seed_<k>/result-TAIRA.csv
"""

from __future__ import annotations

import argparse
import logging
import math
import os

import pandas as pd
import yaml
from datetime import datetime

from core.manager_core import TAIRAManager
from agents.item_retrieval_agent import ItemRetrievalAgent
from agents.searcher_agent import SearcherAgent
from agents.interact_agent import InteractorAgent
from agents.task_interpreter_agent import InterpreterAgent
from utils.memory import Memory

pd.set_option("display.width", 1000)
pd.set_option("display.max_colwidth", 1000)
pd.set_option("display.unicode.east_asian_width", True)


def setup_logger(log_file):
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.DEBUG)
    if logger.hasHandlers():
        logger.handlers.clear()
    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(fh)
    return logger


def _rewrite_csv_with_single_mean(results_csv: str, encoding: str = "ISO-8859-1") -> None:
    """Strip prior summary rows (no id) and trailing garbage means; append one fresh mean row."""
    complete_df = pd.read_csv(results_csv, encoding=encoding)
    if "id" not in complete_df.columns:
        return
    data_df = complete_df[complete_df["id"].notna()].copy()
    if data_df.empty:
        return
    numeric_rows = data_df.dropna(subset=["hit_rate", "mrr", "ndcgs", "fail"])
    mean_row = pd.DataFrame(
        {
            "hit_rate": [numeric_rows["hit_rate"].mean()],
            "mrr": [numeric_rows["mrr"].mean()],
            "ndcgs": [numeric_rows["ndcgs"].mean()],
            "fail": [1 - numeric_rows["fail"].mean()],
        }
    )
    out = pd.concat([data_df, mean_row], ignore_index=True)
    out.to_csv(results_csv, index=False, encoding=encoding)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resume-csv",
        default=None,
        help="Stable checkpoint CSV path: created if missing; appended to if present.",
    )
    args = parser.parse_args()

    with open("system_config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    print("Configuration:", {k: v for k, v in config.items() if "KEY" not in k and "CSE" not in k})

    domain = config["DOMAIN"]
    method = config["METHOD"]
    query_number = config["QUERY_NUMBER"]
    domain_path = f"data/{domain}"

    df = pd.read_csv(f"{domain_path}/query_data1.csv", encoding="ISO-8859-1").head(query_number)
    df = df[df["classification"] == 1]

    done_ids: set = set()
    if args.resume_csv:
        results_csv = os.path.abspath(args.resume_csv)
        os.makedirs(os.path.dirname(results_csv), exist_ok=True)
        log_dir = os.path.dirname(results_csv)
        if os.path.exists(results_csv):
            done_csv = pd.read_csv(results_csv, encoding="ISO-8859-1")
            if "id" in done_csv.columns:
                done_ids = set(done_csv["id"].dropna().tolist())
            print(f"Resuming from {results_csv}: {len(done_ids)} queries already done, skipping them.")
        else:
            print(f"Starting new checkpoint at {results_csv}")
    else:
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H_%M_%S")
        log_dir = f"{domain_path}/logs/{method}-{formatted_time}"
        os.makedirs(log_dir, exist_ok=True)
        results_csv = f"{log_dir}/result-{method}-{formatted_time}.csv"

    print(f"Results CSV: {results_csv}")
    print(f"Total queries to run: {len(df) - len(done_ids.intersection(set(df['id'].tolist())))} / {len(df)}")

    memory = Memory()
    item_agent = ItemRetrievalAgent(memory)
    searcher_agent = SearcherAgent()
    interactor_agent = InteractorAgent(memory)
    interpreter = InterpreterAgent(memory)

    completed_this_run = 0

    for index, row in df.iterrows():
        row_id = row.get("id")
        if row_id in done_ids:
            print(f"  Skipping query {index + 1} (id={row_id}, already done)")
            continue

        log_file = f"{log_dir}/log_{index + 1}.log"
        logger = setup_logger(log_file)
        print(f"Processing query {index + 1} (id={row_id})")

        user_input = row["new_query"]
        target_count = row["target_count"]
        targets = row["targets"]
        user_preference = row["preferences"]

        if domain in ["amazon_clothing", "amazon_music"]:
            target_product = f"{row['title']} | {row['category']}"
        elif domain == "amazon_beauty":
            target_product = f"{row['title']} | {row['description']} | {row['category']}"
        elif domain in ["lastfm", "yelp", "movielens", "amazon_book"]:
            target_product = f"{row['title']} | {row['category']}"
        else:
            target_product = "no target"

        all_target_ids = set(str(t).strip() for t in str(targets).split("|") if t.strip())

        try:
            manager = TAIRAManager(
                memory,
                user_input,
                target_product,
                targets,
                target_count,
                user_preference,
                config,
                logger=logger,
            )
            manager.register_agent(item_agent)
            manager.register_agent(searcher_agent)
            manager.register_agent(interactor_agent)
            manager.register_agent(interpreter)

            hit_rate, mrr, ndcg, fail_flag, pattern_key = manager.delegate_task()

            rec_ids = getattr(manager, "_last_rec_ids", [])
            direct_hit = int(bool(all_target_ids & set(str(i) for i in rec_ids)))
            direct_hr10 = direct_hit
            direct_mrr = 0.0
            direct_ndcg = 0.0
            for rank_i, rid in enumerate(rec_ids[:10], start=1):
                if str(rid) in all_target_ids:
                    direct_mrr = 1.0 / rank_i
                    direct_ndcg = 1.0 / math.log2(rank_i + 1)
                    break

            row["hit_rate"] = hit_rate
            row["mrr"] = mrr
            row["ndcgs"] = ndcg
            row["fail"] = 1 if fail_flag else 0
            row["pattern_used"] = pattern_key
            row["direct_hr10"] = direct_hr10
            row["direct_mrr"] = direct_mrr
            row["direct_ndcg"] = direct_ndcg

        except Exception as e:
            error_msg = f"Error processing query {index + 1}: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            import traceback

            traceback.print_exc()
            row["hit_rate"] = 0
            row["mrr"] = 0
            row["ndcgs"] = 0
            row["fail"] = 1
            row["pattern_used"] = "error"
            row["direct_hr10"] = 0
            row["direct_mrr"] = 0.0
            row["direct_ndcg"] = 0.0

        row_df = pd.DataFrame([row])
        if not os.path.exists(results_csv):
            row_df.to_csv(results_csv, mode="w", header=True, index=False, encoding="ISO-8859-1")
        else:
            # Strip old mean rows (no id) before appending a data row
            prev = pd.read_csv(results_csv, encoding="ISO-8859-1")
            if "id" in prev.columns:
                prev = prev[prev["id"].notna()]
                prev.to_csv(results_csv, index=False, encoding="ISO-8859-1")
            row_df.to_csv(results_csv, mode="a", header=False, index=False, encoding="ISO-8859-1")

        completed_this_run += 1
        done_ids.add(row_id)
        memory.remove_data()
        logger.handlers.clear()

    if not os.path.exists(results_csv):
        print("No results CSV found — no queries were processed.")
        return

    _rewrite_csv_with_single_mean(results_csv)

    print(f"\n=== Run complete. Completed this run: {completed_this_run} new queries ===")
    print(f"Results saved to {results_csv}")

    tail = pd.read_csv(results_csv, encoding="ISO-8859-1").tail(1)
    if "id" in tail.columns and pd.notna(tail["id"].iloc[0]):
        print("(Warning: last CSV row still has id; expected a trailing mean/summary row.)")
        return
    print(
        f"Summary row: hit_rate={float(tail['hit_rate'].iloc[0]):.4f}  "
        f"mrr={float(tail['mrr'].iloc[0]):.4f}  ndcg={float(tail['ndcgs'].iloc[0]):.4f}  "
        f"success_rate={float(tail['fail'].iloc[0]):.4f}"
    )


if __name__ == "__main__":
    main()
