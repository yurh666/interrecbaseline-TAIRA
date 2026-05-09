import math
import os
import logging
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
    """Setup logger for each query."""
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    f_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    f_handler.setLevel(logging.DEBUG)
    f_format = logging.Formatter('%(asctime)s - %(message)s')
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)

    return logger


def main():
    # Load configuration
    with open('system_config.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    print("Configuration:", config)

    domain = config['DOMAIN']
    method = config['METHOD']
    query_number = config['QUERY_NUMBER']
    domain_path = f"data/{domain}"

    # Load queries
    df = pd.read_csv(f"{domain_path}/query_data1.csv", encoding='ISO-8859-1').head(query_number)
    df = df[df['classification'] == 1]

    # Setup logging
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H_%M_%S")
    log_dir = f'{domain_path}/logs/{method}-{formatted_time}'
    os.makedirs(log_dir, exist_ok=True)

    results_csv = f'{log_dir}/result-{method}-{formatted_time}.csv'

    # Initialize agents (shared across queries)
    memory = Memory()
    item_agent = ItemRetrievalAgent(memory)
    searcher_agent = SearcherAgent()
    interactor_agent = InteractorAgent(memory)
    interpreter = InterpreterAgent(memory)

    # Process queries
    for index, row in df.iterrows():
        log_file = f'{log_dir}/log_{index + 1}.log'
        logger = setup_logger(log_file)

        print(f"Processing query {index + 1}")

        user_input = row['new_query']
        target_count = row['target_count']
        targets = row['targets']
        user_preference = row['preferences']

        if domain in ["amazon_clothing", "amazon_music"]:
            target_product = f"{row['title']} | {row['category']}"
        elif domain == "amazon_beauty":
            target_product = f"{row['title']} | {row['description']} | {row['category']}"
        elif domain in ["lastfm", "yelp", "movielens", "amazon_book"]:
            target_product = f"{row['title']} | {row['category']}"
        else:
            target_product = "no target"

        # All future_test target IDs for direct ID-matching evaluation
        all_target_ids = set(str(t).strip() for t in str(targets).split("|") if t.strip())

        try:
            # Create manager for this query
            manager = TAIRAManager(
                memory,
                user_input,
                target_product,
                targets,
                target_count,
                user_preference,
                config,
                logger=logger
            )

            # Register agents
            manager.register_agent(item_agent)
            manager.register_agent(searcher_agent)
            manager.register_agent(interactor_agent)
            manager.register_agent(interpreter)

            # Execute
            hit_rate, mrr, ndcg, fail_flag, pattern_key = manager.delegate_task()

            # Direct ID-matching evaluation (same protocol as InterRec, no LLM needed)
            # Get recommended item IDs from manager's last retrieved items
            rec_ids = getattr(manager, '_last_rec_ids', [])
            direct_hit = int(bool(all_target_ids & set(str(i) for i in rec_ids)))
            direct_hr10 = direct_hit  # binary: 0 or 1

            # Compute rank of first hit for MRR/NDCG
            direct_mrr = 0.0
            direct_ndcg = 0.0
            for rank_i, rid in enumerate(rec_ids[:10], start=1):
                if str(rid) in all_target_ids:
                    direct_mrr = 1.0 / rank_i
                    # Binary relevance: NDCG@10 with single relevant item at rank_i equals 1/log2(rank_i+1)
                    direct_ndcg = 1.0 / math.log2(rank_i + 1)
                    break

            row['hit_rate'] = hit_rate
            row['mrr'] = mrr
            row['ndcgs'] = ndcg
            row['fail'] = 1 if fail_flag else 0
            row['pattern_used'] = pattern_key
            # Direct metrics (comparable with InterRec)
            row['direct_hr10'] = direct_hr10
            row['direct_mrr'] = direct_mrr
            row['direct_ndcg'] = direct_ndcg

        except Exception as e:
            error_msg = f"Error processing query {index + 1}: {str(e)}"
            print(error_msg)
            logger.error(error_msg)

            row['hit_rate'] = 0
            row['mrr'] = 0
            row['ndcgs'] = 0
            row['fail'] = 1
            row['pattern_used'] = "error"
            row['direct_hr10'] = 0
            row['direct_mrr'] = 0.0
            row['direct_ndcg'] = 0.0

        # Save result
        row_df = pd.DataFrame([row])
        if not os.path.exists(results_csv):
            row_df.to_csv(results_csv, mode='w', header=True, index=False)
        else:
            row_df.to_csv(results_csv, mode='a', header=False, index=False)

        # Reset memory
        memory.remove_data()
        logger.handlers.clear()

    # Calculate averages
    complete_df = pd.read_csv(results_csv, encoding='ISO-8859-1')
    mean_row = pd.DataFrame({
        'hit_rate': [complete_df['hit_rate'].mean()],
        'mrr': [complete_df['mrr'].mean()],
        'ndcgs': [complete_df['ndcgs'].mean()],
        'fail': [1 - complete_df['fail'].mean()]
    })
    mean_row.to_csv(results_csv, mode='a', header=False, index=False)

    print(f"Results saved to {results_csv}")


if __name__ == "__main__":
    main()
