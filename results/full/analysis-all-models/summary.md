# Results summary

990 scored answers; 22 questions; models: deepseek-v4-flash, gemma-4-26b-a4b-it, gemma-4-31b-it, qwen3.5-397b, qwen3.8-27b; conditions: C0, C1, C2; repetitions per cell: up to 3.

Means over questions (repetitions averaged first), with 95% bootstrap intervals over questions.

## Coverage of the checklist (0-1)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.21 [0.15, 0.28] | 0.92 [0.86, 0.97] | 0.28 [0.19, 0.40] |
| gemma-4-26b-a4b-it | 0.19 [0.13, 0.25] | 0.81 [0.73, 0.89] | 0.24 [0.15, 0.36] |
| gemma-4-31b-it | 0.27 [0.19, 0.36] | 0.82 [0.74, 0.90] | 0.24 [0.15, 0.36] |
| qwen3.5-397b | 0.32 [0.22, 0.43] | 0.88 [0.81, 0.95] | 0.26 [0.17, 0.38] |
| qwen3.8-27b | 0.18 [0.13, 0.22] | 0.95 [0.90, 0.98] | 0.24 [0.14, 0.36] |

## Fabricated claims per answer (judge)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 4.09 [3.48, 4.64] | 0.14 [0.05, 0.24] | 4.33 [3.71, 5.03] |
| gemma-4-26b-a4b-it | 3.15 [2.55, 3.77] | 0.18 [0.06, 0.32] | 1.58 [1.15, 2.03] |
| gemma-4-31b-it | 3.12 [2.50, 3.70] | 0.05 [0.00, 0.12] | 1.55 [1.03, 2.06] |
| qwen3.5-397b | 4.47 [3.71, 5.20] | 0.12 [0.03, 0.23] | 2.83 [2.36, 3.29] |
| qwen3.8-27b | 4.89 [4.23, 5.61] | 0.15 [0.06, 0.26] | 2.45 [1.85, 3.17] |

## Answers with at least one fabricated claim

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.95 [0.86, 1.00] | 0.14 [0.05, 0.24] | 1.00 [1.00, 1.00] |
| gemma-4-26b-a4b-it | 0.95 [0.86, 1.00] | 0.18 [0.06, 0.32] | 0.65 [0.52, 0.79] |
| gemma-4-31b-it | 0.94 [0.86, 1.00] | 0.05 [0.00, 0.12] | 0.62 [0.44, 0.79] |
| qwen3.5-397b | 0.95 [0.86, 1.00] | 0.12 [0.03, 0.23] | 0.92 [0.85, 0.98] |
| qwen3.8-27b | 1.00 [1.00, 1.00] | 0.14 [0.06, 0.23] | 0.86 [0.79, 0.94] |

## Cited provisions that do not exist (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.18 [0.05, 0.33] | 0.01 [0.00, 0.02] | 0.28 [0.16, 0.41] |
| gemma-4-26b-a4b-it | 0.09 [0.00, 0.25] | 0.02 [0.01, 0.04] | 0.00 |
| gemma-4-31b-it | 0.21 [0.00, 0.50] | 0.01 [0.00, 0.04] | 0.17 |
| qwen3.5-397b | 0.21 [0.05, 0.42] | 0.02 [0.01, 0.03] | 0.45 [0.40, 0.50] |
| qwen3.8-27b | 0.81 | 0.02 [0.01, 0.03] | 0.46 [0.15, 0.77] |

## Uncertain items stated as certain (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 1.00 | 0.35 [0.09, 0.63] | 1.00 |
| gemma-4-26b-a4b-it | 0.75 [0.50, 1.00] | 0.42 [0.17, 0.71] | 0.00 |
| gemma-4-31b-it | 1.00 | 0.52 [0.14, 0.86] | 0.50 [0.00, 1.00] |
| qwen3.5-397b | 0.67 [0.33, 1.00] | 0.41 [0.15, 0.67] | 1.00 |
| qwen3.8-27b | 0.50 [0.00, 1.00] | 0.33 [0.00, 0.67] | 1.00 |

## Uncertain items properly flagged (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.00 [0.00, 0.00] | 0.61 [0.31, 0.89] | 0.00 [0.00, 0.00] |
| gemma-4-26b-a4b-it | 0.04 [0.00, 0.11] | 0.41 [0.15, 0.67] | 0.11 [0.00, 0.33] |
| gemma-4-31b-it | 0.00 [0.00, 0.00] | 0.30 [0.07, 0.59] | 0.11 [0.00, 0.33] |
| qwen3.5-397b | 0.07 [0.00, 0.22] | 0.52 [0.26, 0.78] | 0.00 [0.00, 0.00] |
| qwen3.8-27b | 0.07 [0.00, 0.19] | 0.57 [0.30, 0.85] | 0.00 [0.00, 0.00] |

## Verified items hedged without reason (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| gemma-4-26b-a4b-it | 0.05 [0.00, 0.15] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| gemma-4-31b-it | 0.02 [0.00, 0.05] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| qwen3.5-397b | 0.02 [0.00, 0.05] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| qwen3.8-27b | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.07 [0.00, 0.21] |

## Answers with jurisdiction confusion (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.59 [0.44, 0.74] | 0.00 [0.00, 0.00] | 0.83 [0.74, 0.92] |
| gemma-4-26b-a4b-it | 0.80 [0.70, 0.89] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] |
| gemma-4-31b-it | 0.71 [0.56, 0.85] | 0.00 [0.00, 0.00] | 0.98 [0.95, 1.00] |
| qwen3.5-397b | 0.42 [0.29, 0.56] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] |
| qwen3.8-27b | 0.95 [0.91, 1.00] | 0.00 [0.00, 0.00] | 0.98 [0.95, 1.00] |

## Says the decree is silent (3 silent questions)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.22 [0.00, 0.33] |
| gemma-4-26b-a4b-it | 0.67 [0.67, 0.67] | 1.00 [1.00, 1.00] | 0.11 [0.00, 0.33] |
| gemma-4-31b-it | 0.33 [0.00, 1.00] | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] |
| qwen3.5-397b | 0.56 [0.33, 0.67] | 1.00 [1.00, 1.00] | 0.11 [0.00, 0.33] |
| qwen3.8-27b | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] |

## Notes that the text given is not the law in force

| Model | C0 | C1 | C2 |
|---|---|---|---|
| deepseek-v4-flash | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.06 [0.00, 0.14] |
| gemma-4-26b-a4b-it | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.20 [0.09, 0.32] |
| gemma-4-31b-it | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.09 [0.03, 0.17] |
| qwen3.5-397b | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.26 [0.12, 0.39] |
| qwen3.8-27b | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.05 [0.00, 0.12] |

## Paired contrasts (difference per question, pooled over models)

| Contrast | Metric | Difference [95% CI] | Questions |
|---|---|---|---|
| C1 - C0 | Coverage of the checklist (0-1) | +0.64 [+0.57, +0.71] | 22 |
| C1 - C0 | Fabricated claims per answer (judge) | -3.82 [-4.27, -3.32] | 22 |
| C1 - C0 | Answers with at least one fabricated claim | -0.84 [-0.90, -0.75] | 22 |
| C1 - C0 | Cited provisions that do not exist (share) | -0.17 [-0.28, -0.08] | 21 |
| C1 - C0 | Uncertain items stated as certain (share) | -0.65 [-0.96, -0.23] | 4 |
| C1 - C0 | Uncertain items properly flagged (share) | +0.44 [+0.23, +0.67] | 9 |
| C1 - C0 | Verified items hedged without reason (share) | -0.02 [-0.05, +0.00] | 21 |
| C1 - C0 | Answers with jurisdiction confusion (share) | -0.70 [-0.77, -0.62] | 22 |
| C1 - C0 | Says the decree is silent (3 silent questions) | +0.69 [+0.53, +0.80] | 3 |
| C1 - C0 | Notes that the text given is not the law in force | +0.00 [+0.00, +0.00] | 22 |
| C2 - C1 | Coverage of the checklist (0-1) | -0.62 [-0.74, -0.50] | 22 |
| C2 - C1 | Fabricated claims per answer (judge) | +2.42 [+1.98, +2.87] | 22 |
| C2 - C1 | Answers with at least one fabricated claim | +0.69 [+0.59, +0.77] | 22 |
| C2 - C1 | Cited provisions that do not exist (share) | +0.29 [+0.18, +0.41] | 21 |
| C2 - C1 | Uncertain items stated as certain (share) | +0.64 [+0.33, +0.94] | 2 |
| C2 - C1 | Uncertain items properly flagged (share) | -0.44 [-0.66, -0.23] | 9 |
| C2 - C1 | Verified items hedged without reason (share) | +0.01 [+0.00, +0.04] | 19 |
| C2 - C1 | Answers with jurisdiction confusion (share) | +0.96 [+0.93, +0.98] | 22 |
| C2 - C1 | Says the decree is silent (3 silent questions) | -0.91 [-1.00, -0.80] | 3 |
| C2 - C1 | Notes that the text given is not the law in force | +0.13 [+0.09, +0.18] | 22 |
| C2 - C0 | Coverage of the checklist (0-1) | +0.02 [-0.05, +0.10] | 22 |
| C2 - C0 | Fabricated claims per answer (judge) | -1.40 [-1.73, -1.06] | 22 |
| C2 - C0 | Answers with at least one fabricated claim | -0.15 [-0.21, -0.09] | 22 |
| C2 - C0 | Cited provisions that do not exist (share) | -0.07 [-0.27, +0.09] | 12 |
| C2 - C0 | Uncertain items stated as certain (share) | -0.25 [-0.50, +0.00] | 2 |
| C2 - C0 | Uncertain items properly flagged (share) | +0.01 [-0.02, +0.04] | 9 |
| C2 - C0 | Verified items hedged without reason (share) | -0.00 [-0.05, +0.04] | 19 |
| C2 - C0 | Answers with jurisdiction confusion (share) | +0.26 [+0.19, +0.34] | 22 |
| C2 - C0 | Says the decree is silent (3 silent questions) | -0.22 [-0.27, -0.13] | 3 |
| C2 - C0 | Notes that the text given is not the law in force | +0.13 [+0.09, +0.18] | 22 |
