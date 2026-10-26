# Cost report (measured)

Model: gpt-6-luna. Fresh runs on the real Beaufort County records.

| Run | Model calls | Input tokens | Cached input | Output tokens | Cost |
|---|---|---|---|---|---|
| 20261025-233358-public-spending | 7 | 77,133 | 42,503 | 6,351 | $0.0079 |
| 20261025-233400-local-government | 7 | 74,747 | 37,201 | 5,938 | $0.0080 |
| 20261025-233402-growth-development | 10 | 107,436 | 78,834 | 4,742 | $0.0067 |
| 20261025-233404-public-safety | 9 | 115,204 | 89,692 | 4,605 | $0.0064 |

**Typical run (average of 4):** 93,630 input tokens (66% cached), 5,409 output tokens.

gpt-6-luna prices per 1M tokens (Portkey's public price list): input $0.1, cached input $0.01, cache write $0.125, output $0.5.

| | Cost |
|---|---|
| One run | $0.0073 |
| One user per month (20 runs, assumed) | $0.15 |
| 100 users per month | $14.54 |
| 10,000 users per month | $1,453.56 |

Assumption: every run is fresh. Repeat runs served from the app cache cost nothing, so real costs would be lower.

**Spent on the Portkey key so far:** $0.50 across 69 searches and 597 AI calls (building, testing, evaluation, and demos).
