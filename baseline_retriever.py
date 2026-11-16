"""Baseline retriever over threat_records.json.

TF-IDF + cosine similarity. Deliberately simple: pure lexical overlap on
title + description text, no synonym handling, no semantic model, no
reranking. This is the retriever PROBLEM.md asks you to evaluate and
improve -- it is a starting point, not a reference implementation.

Usage:
    python baseline_retriever.py "query text here" --k 5

Requires: scikit-learn (pip install -r requirements.txt)
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CORPUS_PATH = Path(__file__).resolve().parent / "threat_records.json"


@dataclass
class ScoredRecord:
    id: str
    title: str
    category: str
    score: float


class BaselineRetriever:
    """Fits one TF-IDF vectorizer over the corpus at load time; retrieve()
    just scores the query against that fixed matrix. Nothing is cached or
    persisted across runs."""

    def __init__(self, corpus_path: Path = CORPUS_PATH, index_extra_fields: bool = False):
        self.records = json.loads(Path(corpus_path).read_text(encoding="utf-8"))
        self.index_extra_fields = index_extra_fields
        self._texts = [
            f"{r['category']} {self._doc_text(r)} {r['mitigation']}"
            if index_extra_fields
            else self._doc_text(r)
            for r in self.records
        ]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self.vectorizer.fit_transform(self._texts)

    @staticmethod
    def _doc_text(record: dict) -> str:
        return f"{record['title']} {record['description']}"

    def retrieve(self, query: str, k: int = 5) -> list[ScoredRecord]:
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self._matrix)[0]
        ranked = sorted(range(len(self.records)), key=lambda i: sims[i], reverse=True)
        return [
            ScoredRecord(
                id=self.records[i]["id"],
                title=self.records[i]["title"],
                category=self.records[i]["category"],
                score=float(sims[i]),
            )
            for i in ranked[:k]
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the baseline threat retriever.")
    parser.add_argument("query", help="Free-text query.")
    parser.add_argument("--k", type=int, default=5, help="Number of results to return.")
    parser.add_argument(
        "--index-extra-fields", action="store_true"
    )
    args = parser.parse_args()

    retriever = BaselineRetriever(CORPUS_PATH, index_extra_fields=args.index_extra_fields)
    results = retriever.retrieve(args.query, k=args.k)

    print(f"Query: {args.query!r}\n")
    for rank, r in enumerate(results, start=1):
        print(f"{rank}. [{r.score:.3f}] {r.id} — {r.title}  ({r.category})")


if __name__ == "__main__":
    main()
