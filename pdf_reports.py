"""PDF outputs for VentureLens: 1-page committee memo and founder diagnostic."""
from datetime import date

from fpdf import FPDF

LABELS = {
    "market_tam": "Market & TAM",
    "financial_cacltv": "Financial & CAC/LTV",
    "traction_moat": "Traction & Moat",
}

REPLACEMENTS = {
    "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"', "\u2022": "-", "\u2026": "...",
    "\u20b9": "INR ", "\u00a0": " ",
}


def clean(text):
    """Built-in PDF fonts are Latin-1 only, so swap common symbols for plain ones."""
    text = str(text if text is not None else "")
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def as_text(item):
    if isinstance(item, dict):
        return "; ".join(str(v) for v in item.values())
    return str(item)


class Report(FPDF):
    def __init__(self, title, base):
        super().__init__(format="A4")
        self.base = base
        self.lh_mm = base * 0.45 + 0.8
        self.set_margins(18, 16, 18)
        self.set_auto_page_break(auto=True, margin=14)
        self.add_page()
        self.set_font("Helvetica", "B", base + 7)
        self.multi_cell(0, base * 0.5 + 3, clean(title), new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", base - 1)
        self.set_text_color(110, 110, 110)
        self.cell(0, self.lh_mm, f"VentureLens | FICCI FLO pitch screening | {date.today():%d %b %Y}",
                  new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def heading(self, text):
        self.ln(2)
        self.set_font("Helvetica", "B", self.base + 2)
        self.cell(0, self.lh_mm + 2, clean(text), new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", self.base)

    def para(self, text):
        self.set_font("Helvetica", "", self.base)
        self.multi_cell(0, self.lh_mm, clean(text), new_x="LMARGIN", new_y="NEXT")

    def bullets(self, items):
        self.set_font("Helvetica", "", self.base)
        for item in items or []:
            self.set_x(self.l_margin + 3)
            self.multi_cell(0, self.lh_mm, "- " + clean(as_text(item)), new_x="LMARGIN", new_y="NEXT")

    def scorecard(self, result):
        judge = result.get("judge") or {}
        maxes = {s.get("agent"): s.get("max_score") for s in result.get("scorers", [])}
        self.set_font("Helvetica", "", self.base)
        for key, val in (judge.get("sub_scores") or {}).items():
            self.cell(80, self.lh_mm, clean(LABELS.get(key, key)), border="B")
            self.cell(0, self.lh_mm, f"{val} / {maxes.get(key, '?')}", border="B",
                      new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", self.base)
        self.cell(80, self.lh_mm, "Total score")
        self.cell(0, self.lh_mm, f"{judge.get('final_score')}  (cutoff {judge.get('cutoff')})",
                  new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", self.base)


def startup_name(result):
    return (result.get("extracted") or {}).get("founder_info", {}).get("startup_name", "Startup")


def build_memo(result):
    """Returns (pdf_bytes, page_count). Shrinks the text until it fits one page."""
    memo = result.get("memo") or {}
    for base in (10, 9, 8.5, 8, 7.5):
        pdf = Report(f"Due diligence memo: {startup_name(result)}", base)
        pdf.heading("Scorecard")
        pdf.scorecard(result)
        pdf.heading("Summary")
        pdf.para(memo.get("one_pager_summary"))
        pdf.heading("Key strengths")
        pdf.bullets(memo.get("key_strengths"))
        pdf.heading("Operational red flags")
        pdf.bullets(memo.get("operational_red_flags"))
        pdf.heading("Suggested interview questions")
        pdf.bullets(memo.get("suggested_interview_questions"))
        if pdf.page_no() == 1:
            break
    return bytes(pdf.output()), pdf.page_no()


def memo_pdf(result):
    return build_memo(result)[0]


def diagnostic_pdf(result):
    report = result.get("report") or {}
    pdf = Report(f"Founder diagnostic report: {startup_name(result)}", 11)
    if result.get("judge"):
        pdf.heading("Your scorecard")
        pdf.scorecard(result)
    else:
        failed = (result.get("gate") or {}).get("failed_criteria", [])
        pdf.heading("Mandatory requirements not met")
        pdf.bullets(failed)
    pdf.heading("Summary")
    pdf.para(report.get("summary"))
    pdf.heading("Why the application was not selected")
    pdf.bullets(report.get("rejection_drivers"))
    pdf.heading("How to improve")
    pdf.bullets(report.get("improvement_steps"))
    return bytes(pdf.output())
