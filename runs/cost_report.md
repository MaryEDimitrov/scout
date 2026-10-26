# Cost report (measured)

Model: gpt-6-luna. Fresh runs on the real Beaufort County records.

| Run | Model calls | Input tokens | Cached input | Output tokens | Cost |
|---|---|---|---|---|---|
| 20261024-104436-public-spending | 11 | 126,593 | 86,074 | 6,921 | $0.0094 |
| 20261024-104554-development | 10 | 105,804 | 66,279 | 6,952 | $0.0091 |
| 20261024-110114-public-spending | 10 | 102,732 | 65,194 | 6,595 | $0.0086 |
| 20261025-221049-public-spending | 10 | 122,456 | 86,772 | 5,570 | $0.0081 |

**Typical run (average of 4):** 114,396 input tokens (67% cached), 6,510 output tokens.

gpt-6-luna prices per 1M tokens (Portkey's public price list): input $0.1, cached input $0.01, cache write $0.125, output $0.5.

| | Cost |
|---|---|
| One run | $0.0088 |
| One user per month (20 runs, assumed) | $0.18 |
| 100 users per month | $17.60 |
| 10,000 users per month | $1,760.22 |

Assumption: every run is fresh. Repeat runs served from the app cache cost nothing, so real costs would be lower.
