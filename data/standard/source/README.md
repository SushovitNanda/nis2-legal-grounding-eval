# Source of the reference standard

| File | What it is |
|---|---|
| `standard-draft-en-2026-11-14.json` | The standard as its author (B. Lourenço) wrote it: 22 questions in Portuguese and English, 71 checklist items, 79 citations, each with the page of the official PDF and a literal excerpt of the decree-law as evidence. This is the base. |
| `standard-2026-11-15.json` | The same file with her decisions of 15 Nov on the pilot feedback applied by `scripts/apply_revision_2026_11_15.py`: the point of nine items added to six questions (L1-01, L1-03, L1-06, L1-08, L1-09, L1-10), and L1-05 d and L1-07 d reworded as claims. The decisions are hers; the wording was drafted by Sushi and awaits her check. **This is the frozen standard the full run uses.** |
| `check_citations.py` | Her standalone checker: every evidence excerpt must appear on its page. Kept unchanged. |
| `standard-pilot-transcription.json` | The standard the pilot ran on: transcribed by hand from the tables in her PDF before the JSON arrived, with provisional Portuguese questions. Kept only so the pilot can be reproduced. |

`../standard.json` is generated from the source and must not be edited by hand:

```bash
python scripts/import_standard.py --dry-run   # show what would change
python scripts/import_standard.py             # write data/standard/standard.json
python scripts/import_standard.py --frozen    # same, and mark the version as frozen
python -m nis2eval validate                   # schema, citations against the index, evidence on the page
```

The import only renames fields (the mapping is at the top of the script).

## How the two versions compare

The transcription and the author's file agree on every English question, every checklist item,
every status, every citation and every grading note. They differ only in the Portuguese wording of
15 of the 22 questions, where the pilot used provisional translations. The full run uses the
author's wording.

## Three checks on the citations

1. The author checked each citation against the text and attached the excerpt.
2. `check_citations.py` finds each excerpt on its page: 79 citations, 0 misses on her text file.
   Run on our extraction (`data/decree/DL-125-2025.txt`) it reports 5 misses. All five are words
   that the PDF splits at the end of a line ("disponibili-" / "zação"); her text file has them joined.
3. `python -m nis2eval validate` repeats the excerpt test with split words joined (79 of 79 found)
   and, separately, looks up each article, paragraph and point in an index built from the PDF
   (all resolve, and each starts on the stated page).

## If the standard changes after the run has started

Re-run the import, then the same run and score commands. A question whose Portuguese wording
changed is asked again; a question whose checklist, status or grading note changed is judged
again. Nothing else is redone (see `tests/test_resume.py`).
