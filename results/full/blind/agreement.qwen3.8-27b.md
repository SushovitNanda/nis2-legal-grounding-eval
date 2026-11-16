# Judge qwen3.8-27b vs human grader (blind sample)

| Metric | Cohen's kappa | Raw agreement | n |
|---|---|---|---|
| coverage (linear-weighted) | 0.71 | 0.78 | 85 |
| coverage | 0.64 | 0.78 | 85 |
| uncertainty | 0.22 | 0.50 | 8 |
| fab_any | 0.64 | 0.84 | 25 |
| jurisdiction | 0.92 | 0.96 | 25 |

Fabricated-claim counts: mean absolute difference 0.80 over 25 answers (human total 52, judge total 58).