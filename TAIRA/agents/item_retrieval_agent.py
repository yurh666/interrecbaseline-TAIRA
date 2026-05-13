# agents/item_retrieval_agent.py
# InterRec baseline: item-side retrieval uses BAAI/bge-m3 (dense) + BAAI/bge-reranker-base,
# matching the TAIRA paper-style pipeline (BM25-only runs are archived; see results/metrics_bm25_retriever/).
#
# Prerequisite: TAIRA/data/<DOMAIN>/project_embeddings.npy + bge_embedding_manifest.json
# (produce via: python scripts/precompute_bge_embeddings.py --domain …)

import os

import numpy as np
import yaml
import torch

from FlagEmbedding import BGEM3FlagModel, FlagReranker

from .agent import Agent
from utils.task import get_completion
from utils.Prompts import CLOTH_RETRIEVE_PROMPT, PRODUCT_RETRIEVE_PROMPT, BEAUTY_RETRIEVE_PROMPT, MUSIC_RETRIEVE_PROMPT
from utils.memory import Memory
from utils.item_catalog import load_items_metadata


class ItemRetrievalAgent(Agent):
    def __init__(self, memory):
        super().__init__("ItemRetrievalAgent", memory)
        with open("system_config.yaml") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        self.domain = self.config["DOMAIN"]
        bge_model = self.config.get("BGE_M3_MODEL", "BAAI/bge-m3")
        rerank_model = self.config.get("BGE_RERANKER_MODEL", "BAAI/bge-reranker-base")

        npy_path = os.path.join("data", self.domain, "project_embeddings.npy")
        man_path = os.path.join("data", self.domain, "bge_embedding_manifest.json")
        if not os.path.isfile(npy_path) or not os.path.isfile(man_path):
            raise FileNotFoundError(
                f"BGE embeddings missing for domain={self.domain}.\n"
                f"Expected:\n  {npy_path}\n  {man_path}\n"
                "Run on a GPU machine from repo root:\n"
                "  python scripts/precompute_bge_embeddings.py --domain "
                f"{self.domain}\n"
                "Then copy TAIRA/data/<domain>/project_embeddings.npy (+ manifest) here."
            )

        self.projects = load_items_metadata(self.domain, domain_root="data")
        self.item_emb = np.load(npy_path).astype(np.float32)
        if self.item_emb.shape[0] != len(self.projects):
            raise ValueError(
                f"Embedding rows {self.item_emb.shape[0]} != metadata rows {len(self.projects)} "
                f"for domain={self.domain}; regenerate embeddings."
            )

        use_fp16 = bool(torch.cuda.is_available())
        print(f"ItemRetrievalAgent: loading BGE-M3 ({bge_model}) use_fp16={use_fp16} …")
        self._bge = BGEM3FlagModel(bge_model, use_fp16=use_fp16)
        print(f"ItemRetrievalAgent: loading reranker ({rerank_model}) …")
        self._reranker = FlagReranker(rerank_model, use_fp16=use_fp16)
        print("ItemRetrievalAgent: BGE index ready.")

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

    def execute_task(self, query):
        top_k = self.config["TOPK_ITEMS"]
        top_n = self.config["TOPN_ITEMS"]

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
        result = result.rename(columns={"product_id": "id"})
        return result
