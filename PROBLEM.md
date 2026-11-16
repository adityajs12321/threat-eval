# Retrieval evaluation for a threat-knowledge RAG

## Context

A security platform retrieves relevant "threat records" from a knowledge base to feed into an LLM that drafts threat models for a given system description. Retrieval runs before any LLM call — whatever it returns is what the downstream model gets to work with, so retrieval quality caps the quality of everything built on top of it.

You're given:

- `threat_records.json` — a corpus of 30 threat-knowledge records (the retrieval corpus). Each record has an `id`, `title`, `description`, `category`, and `mitigation`.
- `baseline_retriever.py` — a basic retriever over this corpus.

Your job is **not** to build a better retriever from scratch. It's to determine whether the one you're given is good enough, show your reasoning with real measurements, and make one targeted improvement.

## What "relevant" means here

A threat record is relevant to a query if it describes the same underlying weakness or attack as the query — not just the same broad category. Two records in the same category can both be irrelevant to a specific query if they describe a different mechanism or target. Conversely, two records in *different* categories can both be genuinely relevant to the same query if they describe the same underlying problem from different angles (this corpus has a few deliberate cases like that — we're not telling you which).

## Deliverables

You will submit exactly three things.

### 1. Evaluation harness

Write your own gold set: 10-15 realistic queries (the kind of thing a system description or threat title might say), and for each, hand-label which record `id`s in the corpus are actually relevant. Then implement retrieval metrics — precision@k and recall@k at minimum; add others if you think they add signal — and run them against the provided retriever.

**Submit:** your gold set (queries + labels, with a one-line reason per label), your metrics code, and the resulting numbers.

### 2. Failure analysis

Look at the specific queries where the retriever underperforms, not just the aggregate score. Write up what's actually going wrong — vocabulary mismatch, confusion between near-duplicate records, a category that's systematically under- or over-retrieved, something else. Ground this in concrete examples: the query, what it retrieved, what it should have retrieved.

**Submit:** a short write-up. Half a page to a page is plenty — we're not scoring length.

### 3. One targeted improvement

Make one concrete, scoped change aimed at the specific failure you identified in Deliverable 2 — not a rewrite of the retriever. Re-run the *same* gold set and metrics from Deliverable 1, unchanged, and report before/after numbers. If your change doesn't help, or helps some queries while hurting others, say so plainly.

**Submit:** your changed code, and the before/after numbers produced using the same methodology as Deliverable 1.

## What we are not asking for

- A production-grade retriever. A scrappy, well-reasoned one with a real evaluation behind it beats an elaborate one with no evaluation.
- A large gold set. 10-15 well-considered labels beat 50 rushed ones.
- Multiple improvements. Pick the one you think matters most and go deep on it.

## Time box

Plan for 4-6 hours. If you're well past that and still going, stop, write down what you'd do next, and submit what you have. We'd rather see your judgment on a partial solution than a rushed complete one.

## Submission

A folder or repo link containing: your gold set, your eval code, your write-up, your changed retriever code, and instructions to reproduce your before/after numbers from scratch.
