# Results summary

90 scored answers; 10 questions; models: gemma-4-31b-it, qwen3.5-397b, qwen3.8-27b; conditions: C0, C1, C2; repetitions per cell: up to 1.

Means over questions (repetitions averaged first), with 95% bootstrap intervals over questions.

## Coverage of the checklist (0-1)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| gemma-4-31b-it | 0.09 [0.03, 0.17] | 0.62 [0.45, 0.80] | 0.00 [0.00, 0.00] |
| qwen3.5-397b | 0.07 [0.00, 0.13] | 0.67 [0.53, 0.80] | 0.04 [0.00, 0.10] |
| qwen3.8-27b | 0.06 [0.00, 0.15] | 0.88 [0.82, 0.95] | 0.02 [0.00, 0.05] |

## Fabricated claims per answer (judge)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| gemma-4-31b-it | 3.10 [1.90, 4.40] | 0.00 [0.00, 0.00] | 1.50 [0.60, 2.40] |
| qwen3.5-397b | 4.60 [3.40, 5.80] | 0.10 [0.00, 0.30] | 3.30 [2.60, 4.00] |
| qwen3.8-27b | 4.00 [3.00, 4.90] | 0.30 [0.00, 0.60] | 2.90 [2.00, 3.80] |

## Answers with at least one fabricated claim

| Model | C0 | C1 | C2 |
|---|---|---|---|
| gemma-4-31b-it | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] | 0.60 [0.30, 0.90] |
| qwen3.5-397b | 1.00 [1.00, 1.00] | 0.10 [0.00, 0.30] | 1.00 [1.00, 1.00] |
| qwen3.8-27b | 1.00 [1.00, 1.00] | 0.30 [0.00, 0.60] | 0.90 [0.70, 1.00] |

## Cited provisions that do not exist (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| gemma-4-31b-it | 0.50 | 0.00 [0.00, 0.00] | 0.00 |
| qwen3.5-397b | 0.00 [0.00, 0.00] | 0.01 [0.00, 0.04] | n/a |
| qwen3.8-27b | 1.00 | 0.01 [0.00, 0.02] | 1.00 [1.00, 1.00] |

## Uncertain items stated as certain (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| gemma-4-31b-it | n/a | 1.00 | n/a |
| qwen3.5-397b | n/a | 1.00 | n/a |
| qwen3.8-27b | n/a | 0.33 [0.00, 1.00] | n/a |

## Uncertain items properly flagged (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| gemma-4-31b-it | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| qwen3.5-397b | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| qwen3.8-27b | 0.00 [0.00, 0.00] | 0.38 [0.00, 0.75] | 0.00 [0.00, 0.00] |

## Verified items hedged without reason (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| gemma-4-31b-it | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | n/a |
| qwen3.5-397b | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| qwen3.8-27b | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 |

## Answers with jurisdiction confusion (share)

| Model | C0 | C1 | C2 |
|---|---|---|---|
| gemma-4-31b-it | 0.80 [0.50, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] |
| qwen3.5-397b | 0.60 [0.30, 0.90] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] |
| qwen3.8-27b | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] |

## Notes that the text given is not the law in force

| Model | C0 | C1 | C2 |
|---|---|---|---|
| gemma-4-31b-it | 0.10 [0.00, 0.30] | 0.00 [0.00, 0.00] | 0.20 [0.00, 0.50] |
| qwen3.5-397b | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.40 [0.10, 0.70] |
| qwen3.8-27b | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.20 [0.00, 0.50] |

## Paired contrasts (difference per question, pooled over models)

| Contrast | Metric | Difference [95% CI] | Questions |
|---|---|---|---|
| C1 - C0 | Coverage of the checklist (0-1) | +0.65 [+0.53, +0.76] | 10 |
| C1 - C0 | Fabricated claims per answer (judge) | -3.77 [-4.70, -2.87] | 10 |
| C1 - C0 | Answers with at least one fabricated claim | -0.87 [-0.97, -0.77] | 10 |
| C1 - C0 | Cited provisions that do not exist (share) | -0.42 [-1.00, +0.00] | 3 |
| C1 - C0 | Uncertain items properly flagged (share) | +0.12 [+0.00, +0.25] | 4 |
| C1 - C0 | Verified items hedged without reason (share) | +0.00 [+0.00, +0.00] | 6 |
| C1 - C0 | Answers with jurisdiction confusion (share) | -0.80 [-0.90, -0.70] | 10 |
| C1 - C0 | Notes that the text given is not the law in force | -0.03 [-0.10, +0.00] | 10 |
| C2 - C1 | Coverage of the checklist (0-1) | -0.71 [-0.84, -0.57] | 10 |
| C2 - C1 | Fabricated claims per answer (judge) | +2.43 [+1.90, +2.97] | 10 |
| C2 - C1 | Answers with at least one fabricated claim | +0.70 [+0.50, +0.87] | 10 |
| C2 - C1 | Cited provisions that do not exist (share) | +0.75 [+0.49, +1.00] | 2 |
| C2 - C1 | Uncertain items properly flagged (share) | -0.12 [-0.25, +0.00] | 4 |
| C2 - C1 | Verified items hedged without reason (share) | +0.00 [+0.00, +0.00] | 2 |
| C2 - C1 | Answers with jurisdiction confusion (share) | +1.00 [+1.00, +1.00] | 10 |
| C2 - C1 | Notes that the text given is not the law in force | +0.27 [+0.10, +0.43] | 10 |
| C2 - C0 | Coverage of the checklist (0-1) | -0.05 [-0.11, -0.02] | 10 |
| C2 - C0 | Fabricated claims per answer (judge) | -1.33 [-2.43, -0.27] | 10 |
| C2 - C0 | Answers with at least one fabricated claim | -0.17 [-0.30, -0.03] | 10 |
| C2 - C0 | Uncertain items properly flagged (share) | +0.00 [+0.00, +0.00] | 4 |
| C2 - C0 | Verified items hedged without reason (share) | +0.00 [+nan, +nan] | 1 |
| C2 - C0 | Answers with jurisdiction confusion (share) | +0.20 [+0.10, +0.30] | 10 |
| C2 - C0 | Notes that the text given is not the law in force | +0.23 [+0.07, +0.40] | 10 |
