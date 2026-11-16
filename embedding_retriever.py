"""Dense-embedding retriever over threat_records.json.

Usage:
    python embedding_retriever.py "query text here" --k 5
    python embedding_retriever.py "query" --model BAAI/bge-small-en-v1.5
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

from baseline_retriever import CORPUS_PATH, BaselineRetriever, ScoredRecord

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"

class EmbeddingRetriever:
    """Embeds every record once at load time"""

    def __init__(self, corpus_path: Path = CORPUS_PATH, model_name: str = DEFAULT_MODEL):
        self.records = json.loads(Path(corpus_path).read_text(encoding="utf-8"))
        self.model = SentenceTransformer(model_name)
        texts = [self._doc_text(r) for r in self.records]
        self._matrix = self.model.encode(texts, normalize_embeddings=True)

    @staticmethod
    def _doc_text(record: dict) -> str:
        return f"{record['category']}: {BaselineRetriever._doc_text(record)}"

    def retrieve(self, query: str, k: int = 5) -> list[ScoredRecord]:
        q_vec = self.model.encode([query], normalize_embeddings=True)[0]
        sims = self._matrix @ q_vec
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
    parser = argparse.ArgumentParser(description="Query the embedding threat retriever.")
    parser.add_argument("query")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Default {DEFAULT_MODEL}.")
    args = parser.parse_args()

    results = EmbeddingRetriever(CORPUS_PATH, args.model).retrieve(args.query, k=args.k)
    print(f"Query: {args.query!r}\n")
    for rank, r in enumerate(results, start=1):
        print(f"{rank}. [{r.score:.3f}] {r.id} — {r.title}  ({r.category})")


if __name__ == "__main__":
    main()
