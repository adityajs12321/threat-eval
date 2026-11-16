# Threat-record retrieval evaluation

## Files

| File | What it is |
|---|---|
| `gold_set.json` | 15 queries, each with relevant record ids (one-line reason per label) and labelled near-misses |
| `evaluate.py` | Runs a retriever over the gold set and reports P@k, R@k, MRR and nDCG per query and on average |
| `baseline_retriever.py` | Provided TF-IDF retriever. `--index-extra-fields` also indexes `category` and `mitigation` |
| `embedding_retriever.py` | Sentence-embedding retriever (`all-MiniLM-L6-v2`) over category + title + description |
| `FAILURE_ANALYSIS.md` | Where and why the baseline fails |

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Running the evaluation

```bash
.venv/bin/python evaluate.py --retriever baseline       --k 1 3 5 10
.venv/bin/python evaluate.py --retriever baseline-extra --k 1 3 5 10
.venv/bin/python evaluate.py --retriever embedding      --k 1 3 5 10
```

| `--retriever` | Scoring | Indexed text |
|---|---|---|
| `baseline` | TF-IDF cosine | title + description (as provided) |
| `baseline-extra` | TF-IDF cosine | category + title + description + mitigation |
| `embedding` | MiniLM embedding cosine | category + title + description |

Each run prints, per query, the four metrics, hits / relevant, which relevant ids were missed, and the top-k ids retrieved, then the mean over queries. With several `--k` values, a summary table follows.

To query a retriever directly:

```bash
.venv/bin/python baseline_retriever.py "Chat unfurl bot requests whatever link a user posts" --k 5
.venv/bin/python baseline_retriever.py "..." --k 5 --index-extra-fields
.venv/bin/python embedding_retriever.py "..." --k 5
```

## Metrics

All metrics use binary relevance from `gold_set.json` and are averaged over the 15 queries.

- **Precision@k** = hits in top k / k (standard, unnormalised). k is capped only at the corpus size (30). Most queries have 1–3 relevant records, so even a perfect retriever can't reach 1.0: the best achievable mean on this gold set is **P@1 1.000, P@3 0.622, P@5 0.373, P@10 0.187**.
- **Recall@k** = hits in top k / number of relevant records.
- **MRR@k** = 1 / rank of the first relevant record (0 if none in the top k).
- **nDCG@k** = DCG / ideal DCG, where a hit at rank i contributes 1 / log2(i + 1).

## Results

### Averages

| Retriever | k | P@k | R@k | MRR | nDCG |
|---|---|---|---|---|---|
| baseline | 1 | 0.467 | 0.300 | 0.467 | 0.467 |
| baseline | 3 | 0.289 | 0.622 | 0.600 | 0.518 |
| baseline | 5 | 0.213 | 0.700 | 0.617 | 0.561 |
| baseline | 10 | 0.120 | 0.756 | 0.617 | 0.585 |
| baseline-extra | 1 | 0.667 | 0.422 | 0.667 | 0.667 |
| baseline-extra | 3 | 0.378 | 0.733 | 0.789 | 0.660 |
| baseline-extra | 5 | 0.253 | 0.800 | 0.789 | 0.691 |
| baseline-extra | 10 | 0.147 | 0.867 | 0.789 | 0.720 |
| embedding | 1 | 0.800 | 0.556 | 0.800 | 0.800 |
| embedding | 3 | 0.489 | 0.867 | 0.867 | 0.832 |
| embedding | 5 | **0.320** | **0.911** | **0.880** | **0.857** |
| embedding | 10 | 0.167 | 0.933 | 0.880 | 0.867 |

Change at k=5 relative to the baseline:

| | ΔP@5 | ΔR@5 | ΔMRR | ΔnDCG@5 | Queries better / same / worse (nDCG@5) |
|---|---|---|---|---|---|
| baseline-extra | +0.040 | +0.100 | +0.172 | +0.130 | 7 / 6 / 2 |
| embedding | +0.107 | +0.211 | +0.263 | +0.296 | 11 / 4 / 0 |

### Per query (nDCG@5, hits / relevant)

| Query | baseline | baseline-extra | embedding |
|---|---|---|---|
| Q01 IDOR / BOLA | 0.65 (2/3) | **0.47 (1/3)** ▼ | 0.67 (2/3) |
| Q02 SSRF via link unfurl | 0.00 (0/3) | 0.23 (1/3) | 0.18 (1/3) |
| Q03 XXE in .docx import | 0.50 (1/1) | 1.00 (1/1) | 1.00 (1/1) |
| Q04 credentials exposed | 0.20 (1/3) | 0.47 (1/3) | 1.00 (3/3) |
| Q05 TLS validation off | 1.00 (1/1) | 1.00 (1/1) | 1.00 (1/1) |
| Q06 session fixation | 0.50 (1/1) | 0.50 (1/1) | 1.00 (1/1) |
| Q07 2FA bypass | 0.50 (1/1) | 0.63 (1/1) | 1.00 (1/1) |
| Q08 JWT alg confusion | 1.00 (1/1) | 1.00 (1/1) | 1.00 (1/1) |
| Q09 UI-only role check | 0.00 (0/2) | 0.54 (2/2) | 1.00 (2/2) |
| Q10 CSRF | 0.39 (1/2) | 0.85 (2/2) | 0.69 (2/2) |
| Q11 XSS (all variants) | 0.47 (1/3) | 0.47 (1/3) | 1.00 (3/3) |
| Q12 SQL injection | 0.70 (2/3) | 0.70 (2/3) | 0.77 (2/3) |
| Q13 unsafe deserialization | 0.88 (2/2) | 1.00 (2/2) | 0.92 (2/2) |
| Q14 container as root | 1.00 (1/1) | 1.00 (1/1) | 1.00 (1/1) |
| Q15 password-reset takeover | 0.63 (1/1) | **0.50 (1/1)** ▼ | 0.63 (1/1) |

## Indexing category + mitigation (The scoped change):

`--index-extra-fields` is the cheapest fix for the baseline: it adds more words for queries to match. On average it helps (R@5 +0.10), but it is not a uniform improvement.

**Where it helps:**

- **Q09 (UI-only role check) goes 0/2 → 2/2, but T-018 is found through the word "non"** (from "non-admin" in its mitigation). This is the same token that made the baseline rank the wrong record first ("non-owners" vs "non-cryptographic"). A CSRF record (T-019) still ranks first on "operations". The gain is real on paper but not a sign that the retriever understands the query.
- Q02 finds T-007 via "requests" and "link" in its mitigation; Q03, Q10 and Q13 rank the right records higher.

**Where it hurts:**

- **Q01 (IDOR) loses a relevant record: 2/3 → 1/3.** With mitigation text appended, every record is longer, so each shared term contributes less to the length-normalised TF-IDF score. T-016 (invoice IDOR) shares a single term with the query ("returns"), so the dilution drops it from rank 5 to 7. Meanwhile T-006 (MFA skip) rises to rank 3 on the word "just" from its mitigation. Adding text dilutes real matches and creates new incidental ones.
- **Q15 (password-reset takeover): the correct record drops from rank 2 to 3.** T-027 (MD5 password hashing) repeats "password" in its mitigation ("Rehash all passwords with a slow, salted, purpose-built password hash…") and now outranks T-028.

Mitigation text is written in the corpus's own vocabulary ("egress proxy", "role check", "redact Authorization headers"), not in the words users use to describe systems. So it widens the lexical surface without bridging the vocabulary gap that `FAILURE_ANALYSIS.md` identifies as the main failure.

## Embedding retriever

Embeddings place paraphrases near each other without shared words, so the embedding retriever targets the main failure directly. It improves 11 queries and makes none worse against the baseline. Q04 and Q11 go from 1/3 to 3/3, and Q09 from 0/2 to 2/2.

Category was added to the embedded text after title + description alone scored R@5 0.856 / nDCG 0.811. Category lifted it to 0.911 / 0.857, all from Q04 (2/3 → 3/3) and Q09 (1/2 → 2/2), at a small cost on Q01 (nDCG 0.70 → 0.67, where near-miss T-024 "Privilege Escalation" moves up).

**Still failing:**

- **Q02 (SSRF):** "Chat unfurl bot… VPC" is jargon the small general-purpose model doesn't map to "server fetches URL"; only 1/3 found.
- **Q01:** T-025 (IDOR filed under Privilege Escalation) is still missed.
- **Q12:** T-002 (SQL injection at login) is still missed.
- **Q15:** the CSRF email-change record still outranks the reset token record.
- **Where baseline-extra beats embedding:** Q10 (0.85 vs 0.69) and Q13 (1.00 vs 0.92) rank better with the lexical variant.
