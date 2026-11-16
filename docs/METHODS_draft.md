# Methodology (draft for the report; numbers final)

**Reference standard.** A compliance professional on the team wrote 22 open-ended compliance questions about
Decreto-Lei n.º 125/2025, the Portuguese transposition of Directive (EU) 2022/2555. Each question has a
checklist of what a correct answer must contain (71 items in total, 2 to 5 per question). Every item
carries a citation to article, paragraph and point with the page of the official PDF, and an
*epistemic status*: **verified** (checked in the official text; 60 items), **inferred** (our conclusion,
e.g. a date calculation or the reading of an ambiguous provision; 4 items), or **to confirm** (depends
on regulation, company facts or texts not read; 7 items). Questions were chosen where the decree-law
departs from the directive. Three questions are ones the decree-law itself does not answer. After a pilot on ten questions, the
author revised the standard once, before any answer of the full run was graded: six questions were
extended to ask for points their checklists already contained, and two uncertain items were
reworded as the claim a confident answer would make. The standard was then frozen. Citations
were checked three ways: by the author against the text, with a literal excerpt of the decree
attached to each of the 79 citations; by script, which finds each excerpt on the cited page of the
official PDF; and by script against an index of the decree built independently from the PDF
(article, paragraph and point exist and start on the cited page).

**Conditions.** Each model answered each question under three conditions that differ only in the
document placed before the question: C0, no document; C1, the full official text of the decree-law
(65 pages, 52k to 56k tokens depending on the model's tokeniser); C2, the Portuguese text of the
directive instead of the decree-law (articles and annexes without the recitals, about 42k to 44k
tokens), labelled as the directive. The prompt asked for a complete answer with its legal basis and did not
mention uncertainty. Questions were asked in Portuguese. Each cell was sampled 3 times at
temperature 0.7, giving 22 x 4 x 3 x 3 = 792 answers for the four core models, none missing. A fifth
model was added as a supplementary check (198 answers).

**Models.** Core: qwen3.5-397b, qwen3.8-27b, gemma-4-31b-it, deepseek-v4-flash. Supplementary:
gemma-4-26b-a4b-it. All were called through Adaption's hosted inference API on
14 and 15 November 2026. All test models ran at reasoning effort "medium" with a budget of
12,000 output tokens (reasoning included), a setting that gave every model room to reason and answer.
One model (gemma-4-31b-it) did not reason at all with the setting omitted and does at "medium".
Training cutoffs, from model cards and listings (the models' own statements were inconsistent
between runs): gemma-4-31b-it January 2025, qwen3.5-397b April 2025, deepseek-v4-flash May 2025;
qwen3.8-27b has no published cutoff. Three of the four were therefore trained before the decree-law
was published (4 Dec 2025). Asked without the text what Decreto-Lei n.º 125/2025 is, all four said
they did not know it.

**Scoring.** (i) *Citation check, deterministic.* A parser extracts every article reference from the
answer (Portuguese and English forms, including inverted prose order such as "alínea b) do n.º 1 do
artigo 6.º"), attributes it to the decree, the annexed regime, the directive or another instrument,
and looks it up in the index. The decree-law has two bodies that both start at article 1; the index
keeps them apart. When an answer never names the decree-law and builds on another statute (in trial
runs, models without the text invented a "Decreto-Lei n.º 157/2024"), its bare article references are
attributed to that statute and not checked; when it builds on the Directive, they are attributed to
the Directive and checked against an index of the Directive (46 articles). (ii) *LLM judge.* A fixed
judge model (qwen3.8-27b, temperature 0, reasoning effort "medium") marks each checklist item
as covered, partial or not covered and, separately, whether the answer states it as certain, flags
what it depends on, or hedges without reason; it also lists unsupported claims (any claim with no support in the decree-law or contrary to it; the
rubric calls these "fabricated", and a rule of the Directive stated as Portuguese law is one) and marks
jurisdiction confusion. The judge sees the full official text of the decree-law, the checklist, statuses, grading
notes and the citation-check result, but not the model or condition. In a pilot, a judge shown only
the provisions cited in the checklist marked true statements about other provisions as unsupported;
giving it the full text removed those errors.

*Judges.* The main judge, qwen3.8-27b, and a second judge from another family, gemma-4-31b-it, graded
every answer with the same prompt. Both are also test models, so each result is also reported without the
judge's own answers, the two judges are compared with each other (Table 2), and both are validated
against the blind grades of the author of the standard.

**Metrics.** Coverage (mean item score, partial = 0.5); unsupported claims per answer; share of cited
provisions that do not exist; overconfidence (share of inferred or to-confirm items stated as
certain); proper flagging; unwarranted hedging on verified items; jurisdiction confusion (share of
answers); and, for the three decree-silent questions, whether the answer says the decree does not
settle the point.

**Validation of the judge.** The author of the standard graded a blind sample of 25 answers,
stratified over models and conditions, with the same rubric and without seeing the judge's marks
(A01 to A15 alone, A16 to A25 with the help of an AI assistant).
Agreement (Cohen's kappa, main judge / second judge): item coverage 0.71 / 0.64 (linear-weighted, 85
items); answer has an unsupported claim 0.64 / 0.71; jurisdiction confusion 0.92 / 0.92 (25 answers). Her
marks on uncertain items (8) are too few to estimate agreement. The answer-level marks she entered on a
checklist row were moved to the answer row before scoring; no mark was changed.

**Statistics.** The unit of analysis is the question. Repetitions are averaged within question, and
95% intervals come from 5,000 bootstrap resamples of questions. Condition effects are paired
differences per question. We report the mean standard deviation across repetitions separately.

**Sanity checks.** Parser unit tests on citation formats; a perfect answer and an answer with planted
errors (non-existent article, directive deadline, directive citation) through the scorer; C1 coverage
not below C0 in the pilot.
