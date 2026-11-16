# Results summary

594 scored answers; 22 questions; models: deepseek-v4-flash, qwen3.5-397b, qwen3.8-27b; conditions: C0, C1, C2; repetitions per cell: up to 3.

Means over questions (repetitions averaged first), with 95% bootstrap intervals over questions.

## Coverage of the checklist (0-1)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.16 [0.09, 0.24] | 0.88 [0.81, 0.94] | 0.31 [0.21, 0.43] |
| qwen3.5-397b | 0.24 [0.14, 0.36] | 0.84 [0.76, 0.92] | 0.28 [0.17, 0.40] |
| qwen3.8-27b | 0.10 [0.05, 0.16] | 0.90 [0.84, 0.96] | 0.22 [0.12, 0.34] |

## Fabricated claims per answer (judge)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 4.06 [3.64, 4.45] | 0.08 [0.02, 0.15] | 3.68 [3.29, 4.08] |
| qwen3.5-397b | 4.30 [3.83, 4.88] | 0.30 [0.08, 0.70] | 2.83 [2.47, 3.15] |
| qwen3.8-27b | 3.73 [3.35, 4.14] | 0.21 [0.11, 0.35] | 2.77 [2.30, 3.24] |

## Answers with at least one fabricated claim

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.97 [0.91, 1.00] | 0.06 [0.02, 0.12] | 1.00 [1.00, 1.00] |
| qwen3.5-397b | 0.98 [0.95, 1.00] | 0.17 [0.08, 0.27] | 0.97 [0.91, 1.00] |
| qwen3.8-27b | 1.00 [1.00, 1.00] | 0.15 [0.08, 0.24] | 0.95 [0.88, 1.00] |

## Cited provisions that do not exist (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.18 [0.05, 0.33] | 0.01 [0.00, 0.02] | 0.28 [0.16, 0.41] |
| qwen3.5-397b | 0.21 [0.05, 0.42] | 0.02 [0.01, 0.03] | 0.45 [0.40, 0.50] |
| qwen3.8-27b | 0.81 | 0.02 [0.01, 0.03] | 0.46 [0.15, 0.77] |

## Uncertain items stated as certain (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | n/a | 0.25 [0.00, 0.62] | 1.00 |
| qwen3.5-397b | 1.00 [1.00, 1.00] | 0.17 [0.00, 0.50] | 1.00 |
| qwen3.8-27b | 0.00 | 0.11 [0.00, 0.33] | 1.00 |

## Uncertain items properly flagged (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.00 [0.00, 0.00] | 0.54 [0.24, 0.83] | 0.00 [0.00, 0.00] |
| qwen3.5-397b | 0.00 [0.00, 0.00] | 0.43 [0.17, 0.70] | 0.00 [0.00, 0.00] |
| qwen3.8-27b | 0.04 [0.00, 0.11] | 0.50 [0.22, 0.78] | 0.00 [0.00, 0.00] |

## Verified items hedged without reason (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| qwen3.5-397b | 0.02 [0.00, 0.06] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| qwen3.8-27b | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |

## Answers with jurisdiction confusion (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.82 [0.71, 0.91] | 0.00 [0.00, 0.00] | 0.86 [0.76, 0.94] |
| qwen3.5-397b | 0.85 [0.79, 0.91] | 0.00 [0.00, 0.00] | 0.98 [0.95, 1.00] |
| qwen3.8-27b | 0.98 [0.95, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] |

## Says the decree is silent (3 silent questions)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.33 [0.00, 0.67] |
| qwen3.5-397b | 0.78 [0.67, 1.00] | 1.00 [1.00, 1.00] | 0.11 [0.00, 0.33] |
| qwen3.8-27b | 0.22 [0.00, 0.33] | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] |

## Notes that the text given is not the law in force

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.09 [0.03, 0.15] | 0.00 [0.00, 0.00] | 0.21 [0.11, 0.33] |
| qwen3.5-397b | 0.05 [0.00, 0.12] | 0.00 [0.00, 0.00] | 0.36 [0.21, 0.53] |
| qwen3.8-27b | 0.06 [0.00, 0.14] | 0.00 [0.00, 0.00] | 0.24 [0.12, 0.38] |

## Paired contrasts (difference per question, pooled over models)

| Contrast | Metric | Difference [95% CI] | Questions |
|---|---|---|---|
| C1 - C0 | Coverage of the checklist (0-1) | +0.71 [+0.63, +0.78] | 22 |
| C1 - C0 | Fabricated claims per answer (judge) | -3.83 [-4.22, -3.47] | 22 |
| C1 - C0 | Answers with at least one fabricated claim | -0.86 [-0.91, -0.79] | 22 |
| C1 - C0 | Cited provisions that do not exist (share) | -0.22 [-0.37, -0.10] | 18 |
| C1 - C0 | Uncertain items stated as certain (share) | -0.75 [-1.00, -0.50] | 2 |
| C1 - C0 | Uncertain items properly flagged (share) | +0.48 [+0.23, +0.73] | 9 |
| C1 - C0 | Verified items hedged without reason (share) | -0.01 [-0.03, +0.00] | 20 |
| C1 - C0 | Answers with jurisdiction confusion (share) | -0.88 [-0.93, -0.84] | 22 |
| C1 - C0 | Says the decree is silent (3 silent questions) | +0.67 [+0.56, +0.78] | 3 |
| C1 - C0 | Notes that the text given is not the law in force | -0.07 [-0.12, -0.03] | 22 |
| C2 - C1 | Coverage of the checklist (0-1) | -0.60 [-0.73, -0.48] | 22 |
| C2 - C1 | Fabricated claims per answer (judge) | +2.90 [+2.60, +3.18] | 22 |
| C2 - C1 | Answers with at least one fabricated claim | +0.85 [+0.78, +0.90] | 22 |
| C2 - C1 | Cited provisions that do not exist (share) | +0.30 [+0.19, +0.42] | 21 |
| C2 - C1 | Uncertain items stated as certain (share) | +1.00 [+1.00, +1.00] | 2 |
| C2 - C1 | Uncertain items properly flagged (share) | -0.49 [-0.75, -0.23] | 9 |
| C2 - C1 | Verified items hedged without reason (share) | +0.00 [+0.00, +0.00] | 19 |
| C2 - C1 | Answers with jurisdiction confusion (share) | +0.95 [+0.91, +0.97] | 22 |
| C2 - C1 | Says the decree is silent (3 silent questions) | -0.85 [-1.00, -0.78] | 3 |
| C2 - C1 | Notes that the text given is not the law in force | +0.27 [+0.19, +0.35] | 22 |
| C2 - C0 | Coverage of the checklist (0-1) | +0.10 [+0.02, +0.19] | 22 |
| C2 - C0 | Fabricated claims per answer (judge) | -0.93 [-1.25, -0.65] | 22 |
| C2 - C0 | Answers with at least one fabricated claim | -0.01 [-0.04, +0.01] | 22 |
| C2 - C0 | Cited provisions that do not exist (share) | -0.10 [-0.31, +0.08] | 12 |
| C2 - C0 | Uncertain items stated as certain (share) | +0.00 [+nan, +nan] | 1 |
| C2 - C0 | Uncertain items properly flagged (share) | -0.01 [-0.04, +0.00] | 9 |
| C2 - C0 | Verified items hedged without reason (share) | -0.01 [-0.03, +0.00] | 15 |
| C2 - C0 | Answers with jurisdiction confusion (share) | +0.07 [+0.02, +0.11] | 22 |
| C2 - C0 | Says the decree is silent (3 silent questions) | -0.19 [-0.22, -0.11] | 3 |
| C2 - C0 | Notes that the text given is not the law in force | +0.21 [+0.12, +0.29] | 22 |
