# Threat-record retrieval evaluation

## Files

| File | What it is |
|---|---|
| `gold_set.json` | 15 queries, each with relevant record ids (one-line reason per label) and labelled near-misses |
| `evaluate.py` | Runs a retriever over the gold set and reports P@k, R@k, MRR and nDCG per query and on average |
| `baseline_retriever.py` | Provided TF-IDF retriever. `--index-extra-fields` also indexes `category` and `mitigation` |
| `char_ngram_retriever.py` | **The scoped change:** the baseline with character 3–5-gram TF-IDF and sublinear term frequency |
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
.venv/bin/python evaluate.py --retriever char-ngram     --k 1 3 5 10
.venv/bin/python evaluate.py --retriever embedding      --k 1 3 5 10
```

| `--retriever` | Scoring | Indexed text |
|---|---|---|
| `baseline` | TF-IDF cosine, word tokens | title + description (as provided) |
| `char-ngram` | TF-IDF cosine, character 3–5-grams, sublinear tf | title + description |
| `embedding` | MiniLM embedding cosine | category + title + description |

Each run prints, per query, the four metrics, hits / relevant, which relevant ids were missed, and the top-k ids retrieved, then the mean over queries. With several `--k` values, a summary table follows.

To query a retriever directly:

```bash
.venv/bin/python baseline_retriever.py "Chat unfurl bot requests whatever link a user posts" --k 5
.venv/bin/python char_ngram_retriever.py "..." --k 5
.venv/bin/python embedding_retriever.py "..." --k 5
```

## Metrics

All metrics use binary relevance from `gold_set.json` and are averaged over the 15 queries.

- **Precision@k** = hits in top k / k (standard, unnormalised). k is capped only at the corpus size (30).
  *Measures:* how much of what the LLM receives is relevant, i.e. how much noise is passed downstream. Most queries have 1–3 relevant records, so even a perfect retriever can't reach 1.0: the best achievable mean on this gold set is **P@1 1.000, P@3 0.622, P@5 0.373, P@10 0.187**.
- **Recall@k** = hits in top k / number of relevant records.
  *Measures:* how much of the relevant knowledge makes it into the top k at all. A missed record is a threat the downstream threat model can't mention, so this is the metric that caps output quality.
- **MRR@k** = 1 / rank of the first relevant record (0 if none in the top k).
  *Measures:* how quickly the first useful record appears. 1.0 means a relevant record is ranked first; 0.5 means second. It ignores every relevant record after the first.
- **nDCG@k** = DCG / ideal DCG, where a hit at rank i contributes 1 / log2(i + 1).
  *Measures:* overall ranking quality. It rewards finding all relevant records *and* placing them near the top, scaled so a perfect ranking scores 1.0 whatever the number of relevant records. It is the single best summary when queries have several relevant records.

## Results

### Averages

| Retriever | k | P@k | R@k | MRR | nDCG |
|---|---|---|---|---|---|
| baseline | 1 | 0.467 | 0.300 | 0.467 | 0.467 |
| baseline | 3 | 0.289 | 0.622 | 0.600 | 0.518 |
| baseline | 5 | 0.213 | 0.700 | 0.617 | 0.561 |
| baseline | 10 | 0.120 | 0.756 | 0.617 | 0.585 |
| char-ngram | 1 | 0.733 | 0.456 | 0.733 | 0.733 |
| char-ngram | 3 | 0.444 | 0.811 | 0.856 | 0.753 |
| char-ngram | 5 | 0.280 | 0.833 | 0.856 | 0.765 |
| char-ngram | 10 | 0.147 | 0.856 | 0.856 | 0.775 |
| embedding | 1 | 0.800 | 0.556 | 0.800 | 0.800 |
| embedding | 3 | 0.489 | 0.867 | 0.867 | 0.832 |
| embedding | 5 | **0.320** | **0.911** | **0.880** | **0.857** |
| embedding | 10 | 0.167 | 0.933 | 0.880 | 0.867 |

Change at k=5 relative to the baseline:

| | ΔP@5 | ΔR@5 | ΔMRR | ΔnDCG@5 | Queries better / same / worse (nDCG@5) |
|---|---|---|---|---|---|
| **char-ngram** | **+0.067** | **+0.133** | **+0.239** | **+0.204** | **9 / 6 / 0** |
| embedding | +0.107 | +0.211 | +0.263 | +0.296 | 11 / 4 / 0 |

### Per query (nDCG@5, hits / relevant)

| Query | baseline | baseline-extra | char-ngram | embedding |
|---|---|---|---|---|
| Q01 IDOR / BOLA | 0.65 (2/3) | **0.47 (1/3)** ▼ | 0.95 (3/3) | 0.67 (2/3) |
| Q02 SSRF via link unfurl | 0.00 (0/3) | 0.23 (1/3) | 0.30 (1/3) | 0.18 (1/3) |
| Q03 XXE in .docx import | 0.50 (1/1) | 1.00 (1/1) | 1.00 (1/1) | 1.00 (1/1) |
| Q04 credentials exposed | 0.20 (1/3) | 0.47 (1/3) | 0.47 (1/3) | 1.00 (3/3) |
| Q05 TLS validation off | 1.00 (1/1) | 1.00 (1/1) | 1.00 (1/1) | 1.00 (1/1) |
| Q06 session fixation | 0.50 (1/1) | 0.50 (1/1) | 0.63 (1/1) | 1.00 (1/1) |
| Q07 2FA bypass | 0.50 (1/1) | 0.63 (1/1) | 0.50 (1/1) | 1.00 (1/1) |
| Q08 JWT alg confusion | 1.00 (1/1) | 1.00 (1/1) | 1.00 (1/1) | 1.00 (1/1) |
| Q09 UI-only role check | 0.00 (0/2) | 0.54 (2/2) | 0.61 (1/2) | 1.00 (2/2) |
| Q10 CSRF | 0.39 (1/2) | 0.85 (2/2) | 0.92 (2/2) | 0.69 (2/2) |
| Q11 XSS (all variants) | 0.47 (1/3) | 0.47 (1/3) | 0.77 (2/3) | 1.00 (3/3) |
| Q12 SQL injection | 0.70 (2/3) | 0.70 (2/3) | 0.70 (2/3) | 0.77 (2/3) |
| Q13 unsafe deserialization | 0.88 (2/2) | 1.00 (2/2) | 1.00 (2/2) | 0.92 (2/2) |
| Q14 container as root | 1.00 (1/1) | 1.00 (1/1) | 1.00 (1/1) | 1.00 (1/1) |
| Q15 password-reset takeover | 0.63 (1/1) | **0.50 (1/1)** ▼ | 0.63 (1/1) | 0.63 (1/1) |

## The scoped change: character n-gram TF-IDF

`char_ngram_retriever.py` keeps everything about the baseline except the vectorizer:

```python
TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
```

- **Character n-grams.** Instead of whole words, it indexes overlapping 3–5-character chunks inside each word. Different forms of the same word then share most of their chunks ("owners" / "Owner", "buttons" / "button", "credentials" / "credential", "objects" / "object"). Whole-word TF-IDF has no stemming, so it treats these as unrelated. That was one of the gaps in `FAILURE_ANALYSIS.md`.
- **Sublinear tf** (1 + log tf). Common chunks such as "ion " or "the " repeat many times in every record; without damping, they dominate the score. Without it, character n-grams alone make Q15 worse (8 / 6 / 1 better / same / worse instead of 9 / 6 / 0), so the two settings are treated as one change.
- **Range (3, 5)** is the default. Other ranges are worse, which shows the result is sensitive to this choice: (2, 4) makes 2 queries worse and (4, 6) makes 4 worse.

**Result:** at k=5, R@5 0.700 → 0.833, MRR 0.617 → 0.856, nDCG 0.561 → 0.765. It improves 9 queries and makes none worse.

### Genuine gains

| Query | Record: rank before → after | What now matches |
|---|---|---|
| Q09 UI-only role check | T-024: 25 → **1** | "buttons" ~ "button", "non-owners" ~ "Owner" |
| Q11 XSS | T-015: 10 → 2 | "rendered" ~ "render", "JavaScript" ~ "script" |
| Q13 deserialization | T-021: 4 → 2 | "objects" ~ "object" |
| Q04 credentials exposed | T-011: 4 → 1 | "credentials" ~ "credential", "production" |
| Q03 XXE in .docx import | T-023: 3 → 1 | "importer" ~ "import", "parses" |
| Q10 CSRF | T-019: 2 → 1, T-020: 6 → 3 | "changes" ~ "change", "victim's" |

### Coincidental gains

Character n-grams also match fragments of unrelated words, and `char_wb` doesn't remove stop words. Some of the improvement in the averages comes from this, not from a better understanding of the query:

- **Q01 IDOR, T-025: rank 26 → 5.** This is what takes Q01 from 2/3 to 3/3, and the matching chunks are " get ", " the " and "mber" ("number" in the query vs "member" in the record). The record is genuinely relevant, but it was found through noise.
- **Q02 SSRF, T-007: rank 16 → 2.** It matches on "whatever" (both texts happen to use it) and "post": the query's "a user **posts**" vs the record's HTTP "**POST**". This is the only SSRF record found, so Q02's improvement from 0/3 to 1/3 is mostly luck.
- **Q09, T-018** rises 19 → 14 only through suffixes like "ers ", "ing " and " the ", which doesn't help since it lies outside the top 5.

### Not fixed

- **Wrong record still ranked first:**
  - **Q02:** T-026 (container as root), on "inside", the same incidental word as the baseline.
  - **Q06:** T-020 (CSRF), on "browser" and "victim's".
  - **Q07:** T-002 (SQL-injection login bypass), on "bypass" and "authenticated".
  - **Q15:** T-019 (CSRF email change), on "email" and "account".
- **Doesn't work with true synonyms.** "Unfurl" vs "webhook", "2FA" vs "MFA" and "BOLA" vs "IDOR" share no characters. Q02 still misses T-008 and T-009, and Q04 still misses T-010 and T-012.
- **Hidden regression outside the top 5:** in Q12, T-002 (SQL injection at login) falls from rank 18 to 30, the very last record.

## Embedding retriever

Embeddings place paraphrases near each other without shared words, so the embedding retriever targets the main failure directly. It improves 11 queries and makes none worse against the baseline. Q04 and Q11 go from 1/3 to 3/3, and Q09 from 0/2 to 2/2.

Category was added to the embedded text after title + description alone scored R@5 0.856 / nDCG 0.811. Category lifted it to 0.911 / 0.857, all from Q04 (2/3 → 3/3) and Q09 (1/2 → 2/2), at a small cost on Q01 (nDCG 0.70 → 0.67, where near-miss T-024 "Privilege Escalation" moves up).

**Still failing:**

- **Q02 (SSRF):** "Chat unfurl bot… VPC" is jargon the small general-purpose model doesn't map to "server fetches URL"; only 1/3 found.
- **Q01:** T-025 (IDOR filed under Privilege Escalation) is still missed.
- **Q12:** T-002 (SQL injection at login) is still missed.
- **Q15:** the CSRF email-change record still outranks the reset token record.
