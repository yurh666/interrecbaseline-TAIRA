# agents/item_retrieval_agent.py
# PATCH NOTES (reproduction baseline):
# - Replaced BGE-M3 embedding retrieval + bge-reranker-base with pure BM25 retrieval.
#   Reason: project_embeddings.npy not precomputed (302k items, ~1-2h), bge-reranker-base
#   not cached locally, NLTK punkt unavailable due to network restrictions.
#   Impact: Item retrieval quality may differ from official TAIRA (BM25 vs dense retrieval).
#   Must be disclosed in main table caption.
# - Replaced NLTK word_tokenize with regex tokenizer (punkt not available offline).
# - Fixed base Agent.__init__ memory parameter.
# - Fixed hardcoded llm='gpt-4o-mini' in parse_user_input to use config model.

import os
import re

import numpy as np
import pandas as pd
import yaml
from rank_bm25 import BM25Okapi

from .agent import Agent
from utils.task import get_completion
from utils.Prompts import CLOTH_RETRIEVE_PROMPT, PRODUCT_RETRIEVE_PROMPT, BEAUTY_RETRIEVE_PROMPT, MUSIC_RETRIEVE_PROMPT
from utils.memory import Memory


def _tokenize(text: str):
    """Simple regex tokenizer (replaces NLTK word_tokenize)."""
    return re.findall(r'[a-zA-Z0-9]+', text.lower())


class ItemRetrievalAgent(Agent):
    def __init__(self, memory):
        super().__init__("ItemRetrievalAgent", memory)
        with open('system_config.yaml') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        self.domain = self.config['DOMAIN']
        self.domain_path = "data/" + self.domain

        if self.domain in ["amazon_clothing", "amazon_music", "lastfm", "yelp", "movielens", "amazon_book"]:
            self.df = pd.read_csv(self.domain_path + '/metadata.csv')
            self.df['project_info'] = self.df['title'].fillna('').astype(str) + ' ' + self.df['category'].fillna('').astype(str)
            self.df.rename(columns={'id': 'product_id'}, inplace=True)
        elif self.domain == "amazon_beauty":
            self.df = pd.read_csv(self.domain_path + '/metadata.csv')
            self.df['title'] = self.df['title'].fillna('').astype(str)
            self.df['description'] = self.df['description'].fillna('').astype(str)
            self.df['category'] = self.df['category'].fillna('').astype(str)
            self.df['project_info'] = self.df['title'] + ' ' + self.df['description'] + self.df['category']
            self.df.rename(columns={'id': 'product_id'}, inplace=True)
        else:
            raise ValueError(f"Unsupported domain: {self.domain}")

        self.projects = self.df
        self.corpus = self.df['project_info'].astype(str).tolist()

        # BM25 index over full item catalogue
        print(f"Building BM25 index for {len(self.corpus)} items...")
        tokenized_corpus = [_tokenize(doc) for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)
        print("BM25 index ready.")

    def parse_user_input(self, user_input):
        history = self.memory.get_history() if self.memory else ''
        sys_prompt = "You're a recommendation assistant and you're good at recognizing user preferences."
        prompt = f"The user's personalized preferences are: {self.memory.get_preference() if self.memory and hasattr(self.memory, 'get_preference') else ''}"
        if self.domain == "amazon_clothing":
            prompt += CLOTH_RETRIEVE_PROMPT.replace('{user_input}', user_input)
        elif self.domain == "amazon_beauty":
            prompt += BEAUTY_RETRIEVE_PROMPT.replace('{user_input}', user_input)
        elif self.domain in ["amazon_music", "lastfm"]:
            prompt += MUSIC_RETRIEVE_PROMPT.replace('{user_input}', user_input)
        elif self.domain in ["yelp", "movielens", "amazon_book"]:
            prompt += PRODUCT_RETRIEVE_PROMPT.replace('{user_input}', user_input)

        messages = [{"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}]
        # Use configured model (not hardcoded gpt-4o-mini)
        response = get_completion(messages)
        return response

    def match_projects_with_BM25(self, user_query, top_k=10):
        tokenized_query = _tokenize(user_query)
        scores = self.bm25.get_scores(tokenized_query)
        top_k_indices = np.argsort(scores)[::-1][:top_k]
        top_k_projects = self.projects.iloc[top_k_indices].copy()
        top_k_projects['similarity_score'] = [scores[i] for i in top_k_indices]
        return top_k_projects

    def execute_task(self, query):
        top_k = self.config['TOPK_ITEMS']
        top_n = self.config['TOPN_ITEMS']

        # Step 1: LLM extracts structured preference keywords from the query
        reference = self.parse_user_input(query)

        # Step 2: BM25 retrieval over full catalogue → top_n candidates
        tokenized_query = _tokenize(reference)
        scores = self.bm25.get_scores(tokenized_query)
        top_n_indices = np.argsort(scores)[::-1][:top_n]
        top_n_projects = self.projects.iloc[top_n_indices].copy()
        top_n_projects['similarity_score'] = [scores[i] for i in top_n_indices]

        # Step 3: Re-rank top_n with full query string → top_k
        tokenized_full = _tokenize(query)
        rerank_corpus = top_n_projects['project_info'].astype(str).tolist()
        tokenized_rerank = [_tokenize(doc) for doc in rerank_corpus]
        bm25_rerank = BM25Okapi(tokenized_rerank)
        rerank_scores = bm25_rerank.get_scores(tokenized_full)
        top_k_indices = np.argsort(rerank_scores)[::-1][:top_k]
        top_k_projects = top_n_projects.iloc[top_k_indices].copy()
        top_k_projects['project_info'] = top_k_projects['project_info'].apply(
            lambda x: x[:800] if len(x) > 800 else x
        )
        # PATCH: reset index so DataFrame str() doesn't show raw row-numbers.
        # Rename product_id→id so the InteractorAgent LLM uses the ASIN as item id
        # (matching the {"id": ..., "title": ...} JSON format the evaluator expects).
        result = top_k_projects[['product_id', 'project_info']].reset_index(drop=True)
        result = result.rename(columns={'product_id': 'id'})
        return result
