"""Evaluate a retriever against gold_set.json with precision@k and recall@k.

Usage:
    python evaluate.py --k 5
    python evaluate.py --k 1 3 5 10
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from baseline_retriever import CORPUS_PATH, BaselineRetriever

GOLD_PATH = Path(__file__).resolve().parent / "gold_set.json"


def load_gold(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["queries"] if isinstance(data, dict) else data


def precision_recall_at_k(
    retrieved: list[str], relevant: set[str], k: int, n_docs: int
) -> tuple[float, float, int]:
    k_ret = min(k, n_docs)
    k_prec = min(k_ret, len(relevant))
    hits = len(set(retrieved[:k_ret]) & relevant)
    precision = hits / k_prec if k_prec else 0.0
    recall = hits / len(relevant) if relevant else 0.0
    return precision, recall, hits


def mrr_at_k(retrieved: list[str], relevant: set[str], k: int, n_docs: int) -> float:
    """Reciprocal rank of the first relevant record in the top k (0 if none)."""
    for rank, doc_id in enumerate(retrieved[: min(k, n_docs)], start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int, n_docs: int) -> float:
    """Binary-relevance nDCG@k: DCG of the ranking / DCG of a perfect ranking."""
    k_ret = min(k, n_docs)
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, doc_id in enumerate(retrieved[:k_ret], start=1)
        if doc_id in relevant
    )
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(k_ret, len(relevant)) + 1))
    return dcg / idcg if idcg else 0.0


METRICS = ("precision", "recall", "mrr", "ndcg")


def evaluate(retriever, gold: list[dict], k: int) -> dict:
    n_docs = len(retriever.records)
    rows = []
    for q in gold:
        relevant = {r["id"] for r in q["relevant"]}
        retrieved = [r.id for r in retriever.retrieve(q["query"], k=min(k, n_docs))]
        p, r, hits = precision_recall_at_k(retrieved, relevant, k, n_docs)
        rows.append({
            "qid": q.get("qid", "?"),
            "precision": p,
            "recall": r,
            "mrr": mrr_at_k(retrieved, relevant, k, n_docs),
            "ndcg": ndcg_at_k(retrieved, relevant, k, n_docs),
            "hits": hits,
            "n_relevant": len(relevant),
            "retrieved": retrieved,
            "missed": sorted(relevant - set(retrieved)),
        })
    n = len(rows)
    result = {"k": k, "rows": rows}
    for m in METRICS:
        result[f"mean_{m}"] = sum(x[m] for x in rows) / n
    return result


def print_report(result: dict) -> None:
    k = result["k"]
    print(f"\n=== k = {k} ===")
    print(f"{'qid':<5} {'P@k':>5} {'R@k':>5} {'MRR':>5} {'nDCG':>5} {'hits':>6}  missed / retrieved")
    for x in result["rows"]:
        missed = ",".join(x["missed"]) or "-"
        print(
            f"{x['qid']:<5} {x['precision']:>5.2f} {x['recall']:>5.2f} "
            f"{x['mrr']:>5.2f} {x['ndcg']:>5.2f} "
            f"{x['hits']:>2}/{x['n_relevant']:<3}  missed={missed}  got={x['retrieved']}"
        )
    print(
        f"{'MEAN':<5} {result['mean_precision']:>5.2f} {result['mean_recall']:>5.2f} "
        f"{result['mean_mrr']:>5.2f} {result['mean_ndcg']:>5.2f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the retriever on the gold set.")
    parser.add_argument("--k", type=int, nargs="+", default=[5], help="default 5.")
    parser.add_argument("--gold", type=Path, default=GOLD_PATH)
    parser.add_argument("--corpus", type=Path, default=CORPUS_PATH)
    args = parser.parse_args()

    retriever = BaselineRetriever(args.corpus)
    gold = load_gold(args.gold)
    summary = []
    for k in args.k:
        result = evaluate(retriever, gold, k)
        print_report(result)
        summary.append(result)

    if len(summary) > 1:
        print("\nSummary: ")
        print(f"{'k':>3} {'P@k':>6} {'R@k':>6} {'MRR':>6} {'nDCG':>6}")
        for s in summary:
            print(
                f"{s['k']:>3} {s['mean_precision']:>6.3f} {s['mean_recall']:>6.3f} "
                f"{s['mean_mrr']:>6.3f} {s['mean_ndcg']:>6.3f}"
            )


if __name__ == "__main__":
    main()
