"""Character n-gram TF-IDF retriever over threat_records.json.

Usage:
    python char_ngram_retriever.py "query text here" --k 5
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

from baseline_retriever import CORPUS_PATH, BaselineRetriever


class CharNgramRetriever(BaselineRetriever):
    """BaselineRetriever with a character n-gram vectorizer."""

    def __init__(self, corpus_path: Path = CORPUS_PATH, ngram_range: tuple[int, int] = (3, 5)):
        self.records = json.loads(Path(corpus_path).read_text(encoding="utf-8"))
        self._texts = [self._doc_text(r) for r in self.records]
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=ngram_range, sublinear_tf=True
        )
        self._matrix = self.vectorizer.fit_transform(self._texts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the character n-gram TF-IDF retriever.")
    parser.add_argument("query", help="Free-text query.")
    parser.add_argument("--k", type=int, default=5, help="Number of results to return.")
    args = parser.parse_args()

    results = CharNgramRetriever(CORPUS_PATH).retrieve(args.query, k=args.k)
    print(f"Query: {args.query!r}\n")
    for rank, r in enumerate(results, start=1):
        print(f"{rank}. [{r.score:.3f}] {r.id} — {r.title}  ({r.category})")


if __name__ == "__main__":
    main()
