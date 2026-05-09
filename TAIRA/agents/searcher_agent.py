# agents/searcher_agent.py
# PATCH NOTES (reproduction baseline):
# - Replaced google_search() + bge-reranker-base with BM25 over local knowledge1.csv.
#   Reason: Google Custom Search API unavailable; bge-reranker-base not cached locally.
#   Impact: SearcherAgent still retrieves music-domain attribute knowledge from the same
#   knowledge1.csv file used by the original; only the retrieval method differs (BM25 vs
#   Google Search + neural reranker). This deviates from the official TAIRA setup and must
#   be disclosed in the main table caption.
# - Fixed self.memory bug: original code called self.memory.get_history() in generate_answer()
#   but SearcherAgent() is instantiated without memory in main.py. Now handled gracefully.

import json
import os

import re
import pandas as pd
from rank_bm25 import BM25Okapi


def _tokenize(text: str):
    return re.findall(r'[a-zA-Z0-9]+', text.lower())

from .agent import Agent
from utils.task import get_completion
from utils.task import extract_braces_content

import yaml


class SearcherAgent(Agent):
    def __init__(self):
        super().__init__("SearcherAgent")
        with open('system_config.yaml') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        self.domain = self.config['DOMAIN']
        self.domain_path = "data/" + self.domain

    def _bm25_search(self, query, csv_file_path, num_results=8):
        """BM25 search over local knowledge CSV (Google Search replacement)."""
        if not os.path.exists(csv_file_path):
            return f"No knowledge file at {csv_file_path}"
        df = pd.read_csv(csv_file_path)
        docs = (df['attribute'] + ', ' + df['usage']).tolist()
        tokenized_corpus = [_tokenize(doc) for doc in docs]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = _tokenize(query)
        scores = bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_results]
        results = []
        for i in top_indices:
            results.append(
                f"Attribute: {df.iloc[i]['attribute']}\nUsage: {df.iloc[i]['usage']}"
            )
        return "\n\n".join(results)

    def generate_knowledge(self, input_string, csv_file_path, top_n=20):
        """Retrieve relevant knowledge attributes via BM25, then summarise with LLM."""
        context = self._bm25_search(input_string, csv_file_path, num_results=top_n)

        sys_prompt = (
            "You are a searcher agent and you excel at summarizing unknown knowledge from search results"
        )
        prompt = (
            f"Based on the following search results, provides an insight into the target requirement: \"{input_string}\".\n"
            f"Search Results:\n{context}\n"
            "Please select attributes that best meet target requirements from the search results and "
            "exclude irrelevant attributes that conflict with product type or do not meet requirement "
            "and generate a insight based only on the content of the search results."
            "You should only keep things related to the target demand product, for example, "
            "If the target describes a coat, you should only keep attributes that "
            "describe a coat and remove things related to hats or other clothing types."
            "You can only generate your output based on the words in the Search Results."
            "Don't include content that is not in the search results, even if you think it is in line with the needs. "
            "Output one sentence insight containing all the selected attributes. Don't include too little information."
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt},
        ]
        response = get_completion(messages)
        return response

    def execute_task(self, task):
        query = task
        knowledge_file = self.domain_path + "/knowledge1.csv"
        knowledge = self.generate_knowledge(query, knowledge_file)
        return knowledge
