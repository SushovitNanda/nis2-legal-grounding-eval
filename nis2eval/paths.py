from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONFIG = ROOT / "config"
RESULTS = ROOT / "results"

DECREE_PDF = DATA / "decree" / "DL-125-2025-NIS2.pdf"
DECREE_TXT = DATA / "decree" / "DL-125-2025.txt"
DECREE_INDEX = DATA / "decree" / "dl_index.json"
DIRECTIVE_TXT = DATA / "directive" / "directive-2022-2555-pt.txt"      # C2 document (Portuguese, no recitals)
DIRECTIVE_PDF_EN = DATA / "directive" / "Directive-EU-2022-2555-NIS2-en.pdf"  # official English OJ text (from Bia)
DIRECTIVE_TXT_EN = DATA / "directive" / "directive-2022-2555-en.txt"   # extracted from the PDF, no recitals
DIRECTIVE_INDEX = DATA / "directive" / "directive_index.json"
STANDARD = DATA / "standard" / "standard.json"
RUBRIC = DATA / "standard" / "rubric.md"
SCHEME_TXT = DATA / "stretch" / "situacoes-juridicas.txt"
ARTIFACT_TXT = DATA / "stretch" / "artifact-anonymised.txt"
MODELS = CONFIG / "models.json"
ENV = ROOT / ".env"
