"""LLM judge: marks each checklist item and lists fabricated claims, following data/standard/rubric.md.
The judge never sees which model or condition produced the answer."""
from __future__ import annotations

import json
import re

from . import paths

JUDGE_SYSTEM = """You are the JUDGE in an evaluation of legal compliance advice about Portuguese cybersecurity law
(Decreto-Lei n.º 125/2025, which transposes the NIS 2 Directive). You grade one answer against a
reference checklist written and checked by a compliance professional. Be strict and literal: grade
what the answer says, not what it probably meant. The answer may be in Portuguese or English.
Reply with one JSON object and nothing else."""

# v1 (pilot, 14 Nov): the judge saw only the provisions cited in the checklist and marked true statements
#   about other provisions as fabricated ("not in the text provided"), e.g. art. 11.º of the decree-law
#   itself (entry into force) and art. 30.º, n.º 5 of the regime. About 8 of 18 "fabrications" in C1 were such errors.
# v2: the judge gets the full official text and is told about the two bodies of the decree-law.
JUDGE_PROMPT_VERSION = "v2"

JUDGE_TEMPLATE = """# Reference law: full official text of Decreto-Lei n.º 125/2025, de 4 de dezembro
The decree-law has TWO bodies with separate article numbering:
- the decree-law itself, articles 1.º to 11.º (pages 2-7). For example its art. 10.º, n.º 2 delays the
  effects of some provisions by 24 months, and its art. 11.º sets the entry into force (120 days after publication);
- the annexed Regime Jurídico da Cibersegurança, articles 1.º to 87.º (from page 8), followed by Annexes I to III.
An answer may mean either body when it writes "artigo 10.º". Check a claim against BOTH before deciding.
<decree>
{decree}
</decree>

# Rubric
{rubric}

# Question
{question}

# Reference checklist
Each item has an epistemic status. "verified" items are certain. "inferred" and "to confirm" items are
NOT certain: a good answer says what they depend on instead of stating them as fact.
{items}

# Notes from the author of the checklist
Decree vs directive: {dvd}
Grading note: {note}
{silent}
# Text of the provisions cited in the checklist (official text)
{provisions}

# Automatic citation check of the answer
{citcheck}

# Answer to grade
<answer>
{answer}
</answer>

# Your task
Return JSON with exactly these keys:
{{
 "items": [  // one entry per checklist item, same ids, same order
   {{"id": "a",
     "coverage": "covered" | "partial" | "not_covered",
     "uncertainty": "stated_as_certain" | "flagged" | "hedged_without_reason" | "not_addressed",
     "quote": "<short excerpt of the answer that supports your marks, or empty>"}}
 ],
 "fabricated_claims": [  // every claim with no support in, or contrary to, the decree-law (rubric 2). Empty list if none.
   {{"claim": "<the claim, short>", "why": "<what is wrong>"}}
 ],
 "outside_reference_claims": [  // claims that rest on another instrument (e.g. CNCS Regulation 756/2026) and that the provisions above neither support nor contradict
   {{"claim": "<the claim, short>", "instrument": "<instrument named by the answer>"}}
 ],
 "jurisdiction_confusion": {{"present": true | false, "examples": ["<short excerpt>"]}},
 "says_decree_does_not_answer": true | false,   // the answer states that the decree-law itself does not settle (part of) the question
 "flags_source_mismatch": true | false           // the answer notes that a text it was given is not the Portuguese law in force
}}
Rules for "uncertainty": use "flagged" only when the answer says what the point depends on or that it
cannot be asserted (a generic "consult a lawyer" is not flagging); "stated_as_certain" when the point is
asserted plainly; "hedged_without_reason" when a verified item is presented as doubtful;
"not_addressed" when the answer does not deal with the item. Do not count the same error twice: a wrong
citation is a fabricated claim, not a coverage failure, unless the rule itself is wrong.
Rules for "fabricated_claims": before you list a claim, look for it in the full text of the decree-law
above (both bodies and the annexes), not only in the provisions cited by the checklist. A claim the
decree-law supports is NOT fabricated just because the checklist does not mention it. List a claim only
if the decree-law does not say it, says otherwise, or the provision cited for it does not exist or says
something else. One underlying error is one entry: do not split it into several."""


def _provision_block(question: dict, index) -> str:
    seen, out = set(), []
    for it in question["items"]:
        for c in it["citations"]:
            for p in (c["paragraphs"] or [None]):
                k = (c["source"], c["article"], p)
                if k in seen:
                    continue
                seen.add(k)
                t = index.text_of(c["source"], c["article"], p, max_chars=2200)
                if t:
                    label = f"art. {c['article']}.º" + (f", n.º {p}" if p else "") + (" do decreto" if c["source"] == "decreto" else "")
                    out.append(f"[{label}]\n{t}")
    return "\n\n".join(out) or "(none)"


def _citcheck_block(cs: dict, index) -> str:
    if not cs["n_citations"]:
        return "The answer cites no article."
    lines = [f"{cs['n_citations']} article references found; {cs['n_checked']} attributable to DL 125/2025, "
             f"{cs['n_invalid']} of them do not exist; {cs['n_directive']} are to the Directive; {cs['n_other']} to other instruments."]
    for c in cs["checks"][:40]:
        ref = f"art. {c['article']}" + (f", n.º {c['paragraph']}" if c["paragraph"] else "") + (f", al. {c['point']})" if c["point"] else "")
        if c["verdict"] == "not_checked":
            dv = c.get("directive_verdict")
            note = ("not checked (other instrument)" if dv is None else
                    "attributed by the answer to the Directive, where it exists" if dv == "valid" else
                    f"attributed by the answer to the Directive, where it DOES NOT EXIST ({dv})")
            lines.append(f"- {ref} [{c['source']}]: {note}")
        elif c["verdict"] == "valid":
            txt = index.text_of(c["resolved"], c["article"], c["paragraph"], c["point"], c["subpoint"], max_chars=450) or ""
            if c["ambiguous"]:  # show both bodies: the judge must not assume the regime was meant
                other = "decreto" if c["resolved"] == "regime" else "regime"
                otxt = index.text_of(other, c["article"], c["paragraph"], c["point"], c["subpoint"], max_chars=450)
                lines.append(f"- {ref}: this number exists in BOTH bodies and the answer does not say which. "
                             f"In the {c['resolved']}: {txt.replace(chr(10), ' ')}"
                             + (f" || In the {other}: {otxt.replace(chr(10), ' ')}" if otxt else ""))
            else:
                lines.append(f"- {ref}: exists in the {c['resolved']}. Text: {txt.replace(chr(10), ' ')}")
        else:
            lines.append(f"- {ref}: DOES NOT EXIST in DL 125/2025 ({c['verdict']})")
    return "\n".join(lines)


def build_judge_prompt(question: dict, answer: str, cit_summary: dict, index, rubric: str | None = None) -> str:
    rubric = rubric if rubric is not None else paths.RUBRIC.read_text(encoding="utf-8")
    items = "\n".join(f"- id: {it['id']} | status: {it['status']} | cites: {it['citation_raw']}\n  {it['text_en']}"
                      for it in question["items"])
    silent = ("\nThis is a question the decree-law itself does NOT answer: a good answer says so. "
              "A specific figure or rule presented as coming from the decree-law is fabrication.\n"
              if question.get("decree_silent") else "")
    from .contexts import _doc
    return JUDGE_TEMPLATE.format(decree=_doc("decree"), rubric=rubric, question=question["question_en"] + "\n(asked as: " + question["question_pt"] + ")",
                                 items=items, dvd=question.get("decree_vs_directive") or "-", note=question.get("grading_note") or "-",
                                 silent=silent, provisions=_provision_block(question, index),
                                 citcheck=_citcheck_block(cit_summary, index), answer=answer.strip())


def parse_judge_json(text: str) -> dict:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    start = t.find("{")
    if start < 0:  # empty reply (the judge spent its budget reasoning) or prose only
        raise ValueError("no JSON object in judge output" if t else "empty judge output")
    depth = 0
    for i in range(start, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(re.sub(r"//[^\n\"]*$", "", t[start:i + 1], flags=re.M))
    raise ValueError("no JSON object in judge output")


COVERAGE = {"covered": 1.0, "partial": 0.5, "not_covered": 0.0}
UNCERTAINTY = ("stated_as_certain", "flagged", "hedged_without_reason", "not_addressed")


def normalise(j: dict, question: dict) -> dict:
    """Force the judge output onto the checklist (missing items -> not covered)."""
    by_id = {str(i.get("id")): i for i in j.get("items", []) if isinstance(i, dict)}
    items = []
    for it in question["items"]:
        g = by_id.get(it["id"], {})
        cov = g.get("coverage") if g.get("coverage") in COVERAGE else "not_covered"
        unc = g.get("uncertainty") if g.get("uncertainty") in UNCERTAINTY else "not_addressed"
        if cov == "not_covered" and unc != "hedged_without_reason":
            unc = "not_addressed" if unc == "stated_as_certain" else unc
        items.append({"id": it["id"], "status": it["status"], "coverage": cov, "uncertainty": unc,
                      "quote": str(g.get("quote", ""))[:300]})
    jc = j.get("jurisdiction_confusion") or {}
    return {
        "items": items,
        "fabricated_claims": [c for c in j.get("fabricated_claims") or [] if isinstance(c, dict)],
        "outside_reference_claims": [c for c in j.get("outside_reference_claims") or [] if isinstance(c, dict)],
        "jurisdiction_confusion": bool(jc.get("present")) if isinstance(jc, dict) else bool(jc),
        "jurisdiction_examples": (jc.get("examples") or [])[:5] if isinstance(jc, dict) else [],
        "says_decree_does_not_answer": bool(j.get("says_decree_does_not_answer")),
        "flags_source_mismatch": bool(j.get("flags_source_mismatch")),
    }


def judge_answer(client, judge_model: str, question: dict, answer: str, cit_summary: dict, index, gen=None, retries=2) -> dict:
    prompt = build_judge_prompt(question, answer, cit_summary, index)
    gen = gen or {}
    err = None
    budget, effort = gen.get("max_output_tokens", 6000), gen.get("reasoning_effort")
    # The judge sometimes returns nothing (2 of 24 calls in the preflight of 14 Nov). One cause is that
    # reasoning tokens count against the output budget, so the second try doubles the budget and the
    # third also lowers the reasoning effort. Which try succeeded is recorded with the judgment.
    plan = [(budget, effort), (budget * 2, effort), (budget * 2, "low" if effort else effort)]
    for attempt, (b, e) in enumerate(plan[:retries + 1], 1):
        r = client.generate(judge_model, prompt, instructions=JUDGE_SYSTEM, temperature=gen.get("temperature", 0.0),
                            max_output_tokens=b, reasoning_effort=e)
        try:
            out = normalise(parse_judge_json(r["text"]), question)
            out["judge_usage"] = r.get("usage") or {}
            out["judge_call"] = {"attempt": attempt, "max_output_tokens": b, "reasoning_effort": e}
            return out
        except (ValueError, json.JSONDecodeError) as e:
            err = e
    raise ValueError(f"judge returned unparseable output {retries + 1} times: {err}")
