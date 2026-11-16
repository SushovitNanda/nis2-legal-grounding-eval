# The blind sample: human grades on their own, and against the two judges

25 answers, drawn before any grading, stratified over models and conditions (C0: 8, C1: 9, C2: 8). Graded by the author of the standard, blind to model, condition and the judges' marks.

## 1. By condition: the grader and the two judges on the same answers

| Mark | Graded by | C0 | C1 | C2 |
|---|---|---|---|---|
| Checklist coverage | grader | 12% | 88% | 40% |
|  | qwen3.8-27b | 18% | 85% | 24% |
|  | gemma-4-31b-it | 16% | 85% | 34% |
| Answers with an unsupported claim | grader | 8 of 8 | 2 of 9 | 8 of 8 |
|  | qwen3.8-27b | 8 of 8 | 1 of 9 | 7 of 8 |
|  | gemma-4-31b-it | 8 of 8 | 1 of 9 | 8 of 8 |
| Answers with jurisdiction confusion | grader | 7 of 8 | 0 of 9 | 8 of 8 |
|  | qwen3.8-27b | 6 of 8 | 0 of 9 | 8 of 8 |
|  | gemma-4-31b-it | 8 of 8 | 0 of 9 | 8 of 8 |

## 2. The legal basis the answers rest on (our coding of the grader's notes)

| Legal basis named in the grader's notes | C0 | C1 | C2 |
|---|---|---|---|
| The Directive applied as the law in Portugal | 2 of 8 | 0 of 9 | 7 of 8 |
| A statute that is not the transposition, named as the law in force | 5 of 8 | 0 of 9 | 3 of 8 |
| The repealed regime (Lei n.º 46/2018) | 4 of 8 | 0 of 9 | 0 of 8 |
| Any of the three above (wrong legal basis) | 8 of 8 | 0 of 9 | 8 of 8 |
| Decreto-Lei n.º 125/2025 | 0 of 8 | 9 of 9 | 0 of 8 |
| A claim that CNCS Regulation 756/2026 is not yet published | 0 of 8 | 2 of 9 | 0 of 8 |

## 3. Where a judge and the grader disagree on an answer-level mark

| Answer | Condition | Mark | Grader | qwen3.8-27b | gemma-4-31b-it |
|---|---|---|---|---|---|
| A06 | C0 | jurisdiction confusion | yes | no | yes |
| A11 | C1 | unsupported claim | no | yes | yes |
| A16 | C1 | unsupported claim | yes | no | no |
| A17 | C2 | unsupported claim | yes | no | yes |
| A19 | C0 | jurisdiction confusion | no | no | yes |
| A23 | C1 | unsupported claim | yes | no | no |

Unsupported claims counted over the 25 answers: grader 52, qwen3.8-27b 58, gemma-4-31b-it 48.
