"""BM25 over item catalog ``project_info`` (CPU-friendly fast top-K)."""
from __future__ import annotations

import re

import numpy as np
from rank_bm25 import BM25Okapi


def tokenize_item_text(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", str(text).lower())


class ItemBM25Index:
    def __init__(self, corpus: list[str]):
        self.corpus = list(corpus)
        tokenized = [tokenize_item_text(t) for t in self.corpus]
        if not tokenized:
            tokenized = [[]]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_n: int) -> tuple[np.ndarray, np.ndarray]:
        """Return (indices[int], scores[float]) for top_n docs by BM25."""
        q_tok = tokenize_item_text(query)
        scores = np.asarray(self.bm25.get_scores(q_tok), dtype=np.float64)
        n = min(top_n, len(scores))
        if n <= 0:
            return np.array([], dtype=np.int64), np.array([], dtype=np.float64)
        order = np.argsort(scores)[::-1][:n]
        return order, scores[order]
