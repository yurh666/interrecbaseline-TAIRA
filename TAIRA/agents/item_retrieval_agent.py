# agents/item_retrieval_agent.py
# InterRec / TAIRA baseline (inference):
# - Default ``ITEM_RETRIEVAL_RANKING_BACKEND: bm25``: BM25 on item ``project_info`` (CPU) for every path; LLM for prompts.
# - Optional ``ITEM_RETRIEVAL_RANKING_BACKEND: bge``: dense + rerank (GPU) when reproducing hybrid experiments.
#
# Offline GPU: scripts/precompute_bge_embeddings.py (BGE-M3 item embeddings only).

from __future__ import annotations

import os

import numpy as np
import yaml

from .agent import Agent
from utils.task import get_completion
from utils.Prompts import (
    CLOTH_RETRIEVE_PROMPT,
    PRODUCT_RETRIEVE_PROMPT,
    BEAUTY_RETRIEVE_PROMPT,
    MUSIC_RETRIEVE_PROMPT,
)
from utils.memory import Memory
from utils.embeddings_paths import domain_embedding_artifacts_dir
from utils.item_catalog import load_items_metadata
from utils.item_bm25 import ItemBM25Index


class ItemRetrievalAgent(Agent):
    def __init__(self, memory):
        super().__init__("ItemRetrievalAgent", memory)
        with open("system_config.yaml") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        self.domain = self.config["DOMAIN"]
        bge_model = self.config.get("BGE_M3_MODEL", "BAAI/bge-m3")
        rerank_model = self.config.get("BGE_RERANKER_MODEL", "BAAI/bge-reranker-base")
        self._bge_model_name = bge_model
        self._rerank_model_name = rerank_model

        self.projects = load_items_metadata(self.domain, domain_root="data")
        corpus = self.projects["project_info"].astype(str).tolist()
        self._bm25 = ItemBM25Index(corpus)

        self.item_emb: np.ndarray | None = None
        self._bge = None
        self._reranker = None
        self._bge_ready = False

    def _ensure_bge_stack(self) -> None:
        if self._bge_ready:
            return

        import torch
        from FlagEmbedding import BGEM3FlagModel, FlagReranker

        art = domain_embedding_artifacts_dir(self.domain)
        npy_path = os.path.join(art, "project_embeddings.npy")
        man_path = os.path.join(art, "bge_embedding_manifest.json")
        if not os.path.isfile(npy_path) or not os.path.isfile(man_path):
            raise FileNotFoundError(
                f"BGE embeddings missing for domain={self.domain}.\n"
                f"Expected:\n  {npy_path}\n  {man_path}\n"
                "Run from repo root:\n"
                f"  python scripts/precompute_bge_embeddings.py --domain {self.domain}\n"
                "Or set TAIRA_EMBEDDINGS_ROOT."
            )

        self.item_emb = np.load(npy_path).astype(np.float32)
        if self.item_emb.shape[0] != len(self.projects):
            raise ValueError(
                f"Embedding rows {self.item_emb.shape[0]} != metadata rows {len(self.projects)} "
                f"for domain={self.domain}; regenerate embeddings."
            )

        use_fp16 = bool(torch.cuda.is_available())
        print(f"ItemRetrievalAgent: loading BGE-M3 ({self._bge_model_name}) use_fp16={use_fp16} …")
        self._bge = BGEM3FlagModel(self._bge_model_name, use_fp16=use_fp16)
        print(f"ItemRetrievalAgent: loading reranker ({self._rerank_model_name}) …")
        self._reranker = FlagReranker(self._rerank_model_name, use_fp16=use_fp16)
        print("ItemRetrievalAgent: BGE stack ready.")
        self._bge_ready = True

    def parse_user_input(self, user_input):
        sys_prompt = "You're a recommendation assistant and you're good at recognizing user preferences."
        prompt = f"The user's personalized preferences are: {self.memory.get_preference() if self.memory and hasattr(self.memory, 'get_preference') else ''}"
        if self.domain == "amazon_clothing":
            prompt += CLOTH_RETRIEVE_PROMPT.replace("{user_input}", user_input)
        elif self.domain == "amazon_beauty":
            prompt += BEAUTY_RETRIEVE_PROMPT.replace("{user_input}", user_input)
        elif self.domain in ["amazon_music", "lastfm"]:
            prompt += MUSIC_RETRIEVE_PROMPT.replace("{user_input}", user_input)
        elif self.domain in ["yelp", "movielens", "amazon_book"]:
            prompt += PRODUCT_RETRIEVE_PROMPT.replace("{user_input}", user_input)
        else:
            raise ValueError(f"Unsupported domain: {self.domain}")

        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt}]
        response = get_completion(messages)
        return response

    def _encode_query(self, text: str) -> np.ndarray:
        qv = self._bge.encode([text], batch_size=1)["dense_vecs"].astype(np.float32)
        n = np.linalg.norm(qv, axis=1, keepdims=True)
        n[n == 0] = 1e-12
        return qv / n

    def _use_keyword_path(self, prev_agent_name: str | None) -> bool:
        if (self.config.get("ITEM_RETRIEVAL_KEYWORD_BACKEND") or "bm25").lower() != "bm25":
            return False
        return prev_agent_name == "SearcherAgent"

    def _bm25_should_fallback(self, scores: np.ndarray) -> bool:
        if not self.config.get("BM25_FALLBACK_TO_BGE", True):
            return False
        if scores.size == 0:
            return True
        thr = float(self.config.get("BM25_FALLBACK_MIN_SCORE", 0.0))
        return float(np.max(scores)) <= thr

    def _execute_bm25_only(self, query: str):
        top_k = int(self.config["TOPK_ITEMS"])
        top_n = int(self.config["TOPN_ITEMS"])
        indices, scores = self._bm25.search(query, top_n)
        if indices.size == 0:
            if self.config.get("BM25_FALLBACK_TO_BGE", True):
                print("ItemRetrievalAgent: BM25 empty -> BGE fallback.")
                return self._execute_bge_ranking(query)
            raise RuntimeError("BM25 returned no candidates (enable BM25_FALLBACK_TO_BGE or fix query).")
        if self._bm25_should_fallback(scores):
            if self.config.get("BM25_FALLBACK_TO_BGE", True):
                print("ItemRetrievalAgent: BM25 scores weak -> BGE fallback.")
                return self._execute_bge_ranking(query)

        top_n_projects = self.projects.iloc[indices].copy()
        top_n_projects["_retrieval_score"] = scores
        top_k_projects = top_n_projects.iloc[:top_k].copy()
        top_k_projects["similarity_score"] = top_k_projects["_retrieval_score"].astype(float)

        top_k_projects["project_info"] = top_k_projects["project_info"].apply(
            lambda x: x[:800] if len(str(x)) > 800 else x
        )
        result = top_k_projects[["product_id", "project_info"]].reset_index(drop=True)
        return result.rename(columns={"product_id": "id"})

    def _execute_bge_ranking(self, query: str):
        self._ensure_bge_stack()
        top_k = int(self.config["TOPK_ITEMS"])
        top_n = int(self.config["TOPN_ITEMS"])

        reference = self.parse_user_input(query)
        q_dense = self._encode_query(reference)
        scores = (self.item_emb @ q_dense.T).ravel()
        top_n_indices = np.argsort(scores)[::-1][:top_n]

        top_n_projects = self.projects.iloc[top_n_indices].copy()
        top_n_projects["_dense_score"] = scores[top_n_indices]

        corpus = top_n_projects["project_info"].astype(str).tolist()
        pairs = []
        for doc in corpus:
            doc = doc[:8192] if len(doc) > 8192 else doc
            pairs.append([query, doc])
        rerank_scores = self._reranker.compute_score(pairs)
        if hasattr(rerank_scores, "tolist"):
            rerank_scores = rerank_scores.tolist()
        elif not isinstance(rerank_scores, (list, tuple)):
            rerank_scores = [float(rerank_scores)]
        else:
            rerank_scores = [float(x) for x in rerank_scores]
        rank_order = np.argsort(np.asarray(rerank_scores, dtype=np.float64))[::-1][:top_k]
        top_k_projects = top_n_projects.iloc[rank_order].copy()
        top_k_projects["similarity_score"] = [rerank_scores[i] for i in rank_order]

        top_k_projects["project_info"] = top_k_projects["project_info"].apply(
            lambda x: x[:800] if len(str(x)) > 800 else x
        )
        result = top_k_projects[["product_id", "project_info"]].reset_index(drop=True)
        return result.rename(columns={"product_id": "id"})

    def execute_task(self, query, prev_agent_name=None):
        ranking_be = (self.config.get("ITEM_RETRIEVAL_RANKING_BACKEND") or "bm25").lower()

        if ranking_be == "bm25":
            print(f"ItemRetrievalAgent: BM25 catalog retrieval (prev={prev_agent_name!r}).")
            return self._execute_bm25_only(query)

        if ranking_be != "bge":
            raise ValueError(
                f"Unsupported ITEM_RETRIEVAL_RANKING_BACKEND={ranking_be!r} (expected 'bm25' or 'bge')"
            )

        if self._use_keyword_path(prev_agent_name):
            print(f"ItemRetrievalAgent: keyword path (BM25, prev={prev_agent_name!r}).")
            return self._execute_bm25_only(query)

        print(f"ItemRetrievalAgent: ranking path (BGE+dense+rerank, prev={prev_agent_name!r}).")
        return self._execute_bge_ranking(query)
