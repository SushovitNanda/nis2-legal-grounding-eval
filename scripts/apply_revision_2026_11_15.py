#!/usr/bin/env python3
"""Revision of 15 Nov 2026: Bia's decisions on the pilot feedback, applied to her standard.

    python scripts/apply_revision_2026_11_15.py

Reads  data/standard/source/standard-draft-en-2026-11-14.json  (as she sent it)
Writes data/standard/source/standard-2026-11-15.json

Her decisions (message of 15 Nov):
  2a  L1-05 d and L1-07 d reworded as the claim a confident answer would make; the doubt stays in
      the status and the grading note.
  2b  option 1 on all nine items: add the point to the question.
The decisions are hers; the wording below was drafted by Sushi and is PENDING HER CHECK.
Nothing else in the standard is touched: no citation, no status, no other item or question.
"""
import json
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "data" / "standard" / "source"

QUESTIONS = {
    # item d (notifications go through the electronic platform)
    "L1-01": ("Um incidente com impacto significativo numa entidade importante fica resolvido uma hora depois de ser detetado. "
              "Que notificações tem a entidade de enviar à autoridade de cibersegurança, e por que meio as submete?",
              "A significant incident at an important entity is resolved one hour after it is detected. Which notifications "
              "must the entity send to the cybersecurity authority, and through what channel must it submit them?"),
    # item d (corporate group)
    "L1-03": ("Uma entidade importante já em atividade antes da entrada em vigor do regime tem de designar um responsável de "
              "cibersegurança? Quem pode ser, e em que prazo o comunica? E se a entidade fizer parte de um grupo empresarial?",
              "An important entity already operating before the regime came into force: must it appoint a cybersecurity "
              "officer (responsável de cibersegurança)? Who can it be, and by when must it be communicated? And what if the "
              "entity belongs to a corporate group?"),
    # items a (minimum as well as maximum), b (examples), c (negligence)
    "L1-06": ("Quais são os limites mínimo e máximo da coima por uma contraordenação muito grave praticada por uma pessoa "
              "coletiva que seja entidade importante? Dê exemplos de contraordenações muito graves. E o que acontece em caso "
              "de negligência?",
              "What are the minimum and maximum fines for a very serious administrative offence (contraordenação muito grave) "
              "committed by a legal person that is an important entity? Give examples of very serious offences. And what "
              "happens in case of negligence?"),
    # items c (how they are qualified), d (own measures and fines)
    "L1-08": ("Além das entidades essenciais e importantes, o regime português prevê outra categoria de entidades? Quais? "
              "Como são qualificadas, e que medidas e coimas se lhes aplicam?",
              "Besides essential and important entities, does the Portuguese regime provide for another category of "
              "entities? Which? How are they qualified, and which measures and fines apply to them?"),
    # item d (failing the duties is a serious offence)
    "L1-09": ("Uma empresa já em atividade quando o regime entrou em vigor tem de se identificar junto do CNCS? Em que prazo? "
              "Quem decide se é essencial ou importante? E o que acontece se não cumprir esses deveres?",
              "A company already operating when the regime came into force: must it identify itself to the CNCS? By when? "
              "Who decides whether it is essential or important? And what happens if it does not comply with these duties?"),
    # item c (who sets the minimum measures)
    "L1-10": ("Se o CNCS alterar a qualificação de uma entidade importante, ou as medidas mínimas mudarem, quanto tempo tem a "
              "entidade para se adaptar? E quem define essas medidas mínimas, e segundo que critérios?",
              "If the CNCS changes the qualification of an important entity, or the minimum measures change, how long does "
              "the entity have to adapt? And who sets those minimum measures, and on what criteria?"),
}
ITEMS = {
    "L1-05-d": ("O dever aplica-se a partir de 22/06/2028 (24 meses após o Reg. CNCS n.º 756/2026, de 22/06/2026).",
                "The duty applies from 22/06/2028 (24 months after Reg. CNCS n.º 756/2026 of 22/06/2026)."),
    "L1-07-d": ("A dispensa pode ser pedida até 3/4/2027 (12 meses a contar da entrada em vigor).",
                "The exemption can be requested until 3/4/2027 (12 months from the entry into force)."),
}
NOTES = {
    "L1-05": (" Dúvida do item d: a data só vale se o Reg. CNCS n.º 756/2026 for toda a regulamentação referida no art. 10.º, "
              "n.º 2, do decreto. Data dada como certa = excesso de confiança.",
              " The doubt in item d: the date holds only if Reg. CNCS n.º 756/2026 is all of the regulation referred to in "
              "art. 10.º, n.º 2, of the decree. Date stated as certain = overconfidence."),
    "L1-07": (" Dúvida do item d: os 12 meses podem ser o prazo para pedir ou o período cujos factos a dispensa cobre.",
              " The doubt in item d: the 12 months may be the period to make the request, or the period whose facts the "
              "exemption covers."),
}

d = json.loads((SRC / "standard-draft-en-2026-11-14.json").read_text(encoding="utf-8"))
for q in d["questions"]:
    if q["id"] in QUESTIONS:
        q["question_pt"], q["question_en"] = QUESTIONS[q["id"]]
    if q["id"] in NOTES:
        q["grading_notes"] = (q.get("grading_notes") or "") + NOTES[q["id"]][0]
        q["grading_notes_en"] = (q.get("grading_notes_en") or "") + NOTES[q["id"]][1]
    for it in q["checklist"]:
        if it["id"] in ITEMS:
            it["item_pt"], it["item_en"] = ITEMS[it["id"]]
d["meta"]["date"] = "2026-11-15"
d["meta"]["revision"] = ("15 Nov 2026: decisions of the author on the pilot feedback applied (2a: L1-05 d and L1-07 d reworded "
                         "as claims; 2b: the point of nine items added to six questions: L1-01, L1-03, L1-06, L1-08, L1-09, "
                         "L1-10). Wording drafted by Sushi, pending the author's check.")
out = SRC / "standard-2026-11-15.json"
out.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("wrote", out.name)
