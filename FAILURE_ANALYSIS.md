# Failure analysis:

## 1. Vocabulary mismatch:

TF-IDF can only match identical surface tokens. It has no stemming, synonyms or acronym expansion. Of the 12 relevant records missed at k=5, **10 share zero index terms** with their query (the other two, T-020 and T-015, match only on generic words like "victim" or "browser"). Examples:

| Query | Missed records | Query keywords | Threat record keywords |
|---|---|---|---|
| Q02 "Chat unfurl bot requests whatever link a user posts, from inside the VPC" | T-007 (16), T-008 (17), T-009 (18) | unfurl, link, requests, VPC | webhook, fetch, URL, internal, metadata |
| Q04 "Production credentials end up somewhere a much wider audience…can read them" | T-010 (15), T-012 (16) | credentials, audience | API key, Authorization header, logs; stack trace, password |
| Q09 "Destructive operations are protected only by not showing the buttons…" | T-024 (25), T-018 (19) | buttons, protected, owners | hidden in the UI, no role check |

Missing stemming makes it worse even when the concept is shared: "orders" ≠ "order", "owners" ≠ "owner", "requests" ≠ "request". All of Q02's relevant records rank below 15th, which matters because SSRF is a high-impact threat class.

## 2. One shared word decides the top result

When the overlap is zero or small, a single generic but rare word gets a high IDF weight and wins. The retriever never scores the threat mechanism itself:

- **Q09** ("…protected only by not showing the buttons to non-owners"): rank 1 is T-028 (password reset PRNG) at 0.278, matched solely on **"non"** from "non-owners" vs "non-cryptographic". Ranks 2–5 all score **0.000** and come back in corpus order. There is no score floor, so the retriever returns arbitrary records as confidently as real ones. The correct T-024 and T-018 sit at 25 and 19th rank.
- **Q02**: rank 1 is T-026 (container running as root), matched on **"inside"** ("inside the VPC" vs "inside the container").
- **Q04**: rank 1 is T-022 (pickle cache), matched only on **"read"**.

## 3. Neighbouring threats with shared context outrank the true mechanism

Records that describe the same *setting* (victim, browser, login, search box) but a different *attack* rank above the correct one:

- **Q15** "Account takeover through the forgot-password email link": T-019 (CSRF email change) ranks first on "account" + "email"; the reset-token record T-028 is second.
- **Q10** (CSRF, "riding the victim's existing login"): T-005 (session fixation) ranks first on attacker/page/victim/login. The second CSRF record, T-020, is 6th.
- **Q06** (session fixation): T-020 (CSRF) ranks first on attacker/browser/victim; T-005 is 3rd.
- **Q12** (UNION SQL injection in the search box): T-014 (reflected XSS in *search* results) ranks 2nd, above T-003; T-002 (login SQLi) is 18th.

## Which categories suffer

Recall@5 by category of the relevant record shows the failure is not uniform. **SSRF 0/3, Privilege Escalation 1/3, Secrets Exposure 1/3 and XSS 1/3** are worst. These are exactly the groups whose records describe one problem in very different terms (webhook vs PDF image vs DNS rebinding; logs vs git vs stack traces) that cannot be identified by pure word search. Authentication Bypass, Deserialization and Weak Crypto (3/3, 3/3, 2/2) have distinctive terms ("MFA", "pickle", "MD5") and score fine. The cross-category pairs suffer most: T-025 (IDOR filed as Privilege Escalation) and T-018/T-024 (missing role check split across two categories) are never retrieved.
