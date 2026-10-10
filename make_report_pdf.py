import json
import sys
from pathlib import Path

from pdf_reports import diagnostic_pdf

run = Path("data/output") / (sys.argv[1] if len(sys.argv) > 1 else sorted(p.name for p in Path("data/output").iterdir())[-1])
load = lambda n: json.loads((run / n).read_text(encoding="utf-8"))
result = {
    "extracted": load("01_extraction.json"),
    "scorers": [load("03_market_tam.json"), load("04_financial.json"), load("05_traction.json")],
    "judge": load("06_judge.json"),
    "report": load("07_report.json"),
}
out = run / "founder_diagnostic.pdf"
out.write_bytes(diagnostic_pdf(result))
print("saved", out)
