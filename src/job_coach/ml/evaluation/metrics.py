"""Evaluation module: benchmark retrieval quality and latency."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class EvalResult:
    """Result of a single evaluation query."""

    query: str
    retrieved_texts: list[str]
    relevant_texts: list[str]
    precision_at_k: float
    latency_seconds: float


@dataclass
class BenchmarkReport:
    """Aggregated benchmark results."""

    total_queries: int
    avg_precision_at_k: float
    avg_latency_seconds: float
    results: list[EvalResult] = field(default_factory=list)


def precision_at_k(retrieved: list[str], relevant: list[str], k: int = 5) -> float:
    """Calculate precision@k for a single query.

    Args:
        retrieved: List of retrieved document texts.
        relevant: List of ground-truth relevant texts.
        k: Number of top results to consider.

    Returns:
        Precision@k score between 0.0 and 1.0.
    """
    if not relevant or k == 0:
        return 0.0

    relevant_set = {text.lower().strip() for text in relevant}
    top_k = retrieved[:k]
    hits = sum(1 for text in top_k if text.lower().strip() in relevant_set)
    return hits / k


def run_evaluation(
    queries: list[dict],
    search_fn,
    k: int = 5,
) -> BenchmarkReport:
    """Run evaluation benchmark on a set of queries.

    Args:
        queries: List of dicts with 'query' and 'relevant_texts' keys.
        search_fn: Callable(query: str) -> list[str] that returns retrieved texts.
        k: Top-k to evaluate.

    Returns:
        BenchmarkReport with per-query and aggregated metrics.
    """
    results: list[EvalResult] = []

    for q in queries:
        query_text = q["query"]
        relevant = q.get("relevant_texts", [])

        start = time.perf_counter()
        retrieved = search_fn(query_text)
        latency = time.perf_counter() - start

        p_at_k = precision_at_k(retrieved, relevant, k)

        results.append(
            EvalResult(
                query=query_text,
                retrieved_texts=retrieved[:k],
                relevant_texts=relevant,
                precision_at_k=p_at_k,
                latency_seconds=round(latency, 4),
            )
        )

    avg_p = sum(r.precision_at_k for r in results) / len(results) if results else 0.0
    avg_l = sum(r.latency_seconds for r in results) / len(results) if results else 0.0

    return BenchmarkReport(
        total_queries=len(results),
        avg_precision_at_k=round(avg_p, 4),
        avg_latency_seconds=round(avg_l, 4),
        results=results,
    )
