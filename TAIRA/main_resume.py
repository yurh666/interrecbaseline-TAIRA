"""Checkpoint-aware TAIRA runner.

Drop-in replacement for main.py that supports resuming interrupted runs.
If --resume-csv is given and exists, queries whose original DataFrame index
already appears in that CSV will be skipped; new results are appended to the
same file (no new timestamped dir is created for those queries).

Usage:
  python main_resume.py                         # fresh run (same as main.py)
  python main_resume.py --resume-csv <path>     # resume from existing CSV
"""

import argparse
import logging
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

pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 1000)
pd.set_option('display.unicode.east_asian_width', True)


def setup_logger(log_file):
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.DEBUG)
    if logger.hasHandlers():
        logger.handlers.clear()
    fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)
    return logger


def load_done_indices(resume_csv):
    """Return set of original df indices already present in the resume CSV."""
    if not resume_csv or not os.path.exists(resume_csv):
        return set()
    try:
        done_df = pd.read_csv(resume_csv, encoding='ISO-8859-1')
        if 'id' in done_df.columns:
            return set(done_df['id'].tolist())
        return set()
    except Exception:
        return set()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume-csv', default=None,
                        help='Path to existing result CSV to resume from')
    args = parser.parse_args()

    with open('system_config.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    print("Configuration:", {k: v for k, v in config.items() if 'KEY' not in k and 'CSE' not in k})

    domain = config['DOMAIN']
    method = config['METHOD']
    query_number = config['QUERY_NUMBER']
    domain_path = f"data/{domain}"

    df = pd.read_csv(f"{domain_path}/query_data1.csv", encoding='ISO-8859-1').head(query_number)
    df = df[df['classification'] == 1]

    # Checkpoint: skip already-done rows
    done_ids = set()
    if args.resume_csv and os.path.exists(args.resume_csv):
        results_csv = args.resume_csv
        done_csv = pd.read_csv(results_csv, encoding='ISO-8859-1')
        if 'id' in done_csv.columns:
            done_ids = set(done_csv['id'].dropna().tolist())
        print(f"Resuming from {results_csv}: {len(done_ids)} queries already done, skipping them.")
        log_dir = os.path.dirname(results_csv)
    else:
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H_%M_%S")
        log_dir = f'{domain_path}/logs/{method}-{formatted_time}'
        os.makedirs(log_dir, exist_ok=True)
        results_csv = f'{log_dir}/result-{method}-{formatted_time}.csv'

    print(f"Results CSV: {results_csv}")
    print(f"Total queries to run: {len(df) - len(done_ids)} / {len(df)}")

    memory = Memory()
    item_agent = ItemRetrievalAgent(memory)
    searcher_agent = SearcherAgent()
    interactor_agent = InteractorAgent(memory)
    interpreter = InterpreterAgent(memory)

    completed_this_run = 0

    for index, row in df.iterrows():
        row_id = row.get('id')
        if row_id in done_ids:
            print(f"  Skipping query {index + 1} (id={row_id}, already done)")
            continue

        log_file = f'{log_dir}/log_{index + 1}.log'
        logger = setup_logger(log_file)
        print(f"Processing query {index + 1} (id={row_id})")

        user_input = row['new_query']
        target_count = row['target_count']
        targets = row['targets']
        user_preference = row['preferences']

        if domain in ["amazon_clothing", "amazon_music"]:
            target_product = f"{row['title']} | {row['category']}"
        elif domain == "amazon_beauty":
            target_product = f"{row['title']} | {row['description']} | {row['category']}"
        else:
            target_product = "no target"

        try:
            manager = TAIRAManager(
                memory, user_input, target_product, targets,
                target_count, user_preference, config, logger=logger
            )
            manager.register_agent(item_agent)
            manager.register_agent(searcher_agent)
            manager.register_agent(interactor_agent)
            manager.register_agent(interpreter)

            hit_rate, mrr, ndcg, fail_flag, pattern_key = manager.delegate_task()

            row['hit_rate'] = hit_rate
            row['mrr'] = mrr
            row['ndcgs'] = ndcg
            row['fail'] = 1 if fail_flag else 0
            row['pattern_used'] = pattern_key

        except Exception as e:
            error_msg = f"Error processing query {index + 1}: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            import traceback; traceback.print_exc()
            row['hit_rate'] = 0
            row['mrr'] = 0
            row['ndcgs'] = 0
            row['fail'] = 1
            row['pattern_used'] = "error"

        row_df = pd.DataFrame([row])
        if not os.path.exists(results_csv):
            row_df.to_csv(results_csv, mode='w', header=True, index=False)
        else:
            row_df.to_csv(results_csv, mode='a', header=False, index=False)

        completed_this_run += 1
        memory.remove_data()
        logger.handlers.clear()

    if not os.path.exists(results_csv):
        print("No results CSV found — no queries were processed.")
        return

    # Compute mean over all rows in the CSV (excluding any prior mean row)
    complete_df = pd.read_csv(results_csv, encoding='ISO-8859-1')
    numeric_rows = complete_df.dropna(subset=['hit_rate', 'mrr', 'ndcgs', 'fail'])
    mean_row = pd.DataFrame({
        'hit_rate': [numeric_rows['hit_rate'].mean()],
        'mrr': [numeric_rows['mrr'].mean()],
        'ndcgs': [numeric_rows['ndcgs'].mean()],
        'fail': [1 - numeric_rows['fail'].mean()],
    })
    mean_row.to_csv(results_csv, mode='a', header=False, index=False)

    print(f"\n=== Run complete. Completed this run: {completed_this_run} queries ===")
    print(f"Results saved to {results_csv}")
    print(f"hit_rate={mean_row['hit_rate'].values[0]:.4f}  mrr={mean_row['mrr'].values[0]:.4f}  "
          f"ndcg={mean_row['ndcgs'].values[0]:.4f}  success_rate={mean_row['fail'].values[0]:.4f}")


if __name__ == '__main__':
    main()
