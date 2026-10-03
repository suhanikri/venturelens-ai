from pdf_reports import build_memo, diagnostic_pdf

scorers = [{"agent": "market_tam", "max_score": 30},
           {"agent": "financial_cacltv", "max_score": 30},
           {"agent": "traction_moat", "max_score": 30}]
extracted = {"founder_info": {"startup_name": "EcoCart"}}

accepted = {
    "extracted": extracted, "scorers": scorers,
    "judge": {"final_score": 61, "cutoff": 60,
              "sub_scores": {"market_tam": 19, "financial_cacltv": 22, "traction_moat": 20}},
    "memo": {
        "one_pager_summary": "EcoCart offers an analytics plug-in for online stores to switch to sustainable packaging and track order carbon footprints. It scored 61, barely above the cutoff of 60. Promising momentum, but burn exceeds MRR and the moat is weak.",
        "key_strengths": ["LTV:CAC of 7.11x with healthy margins.", "340 paying merchants.", "22% month-over-month growth."],
        "operational_red_flags": ["Monthly burn of INR 2 Lakhs exceeds MRR of INR 1.5 Lakhs.", "TAM and SAM conflate physical packaging with software spend.", "Weak defensibility."],
        "suggested_interview_questions": ["What is your runway?", "How do you re-estimate software-only TAM?", "What stops an incumbent copying the plug-in?"],
    },
}
rejected = {
    "extracted": extracted, "scorers": scorers,
    "judge": {"final_score": 30, "cutoff": 60,
              "sub_scores": {"market_tam": 8, "financial_cacltv": 12, "traction_moat": 10}},
    "report": {
        "summary": "Your application scored 30 against a cutoff of 60.",
        "rejection_drivers": ["Market size figures lacked supporting data.", "LTV:CAC of 1.2x is below the 2x benchmark."],
        "improvement_steps": ["Build a bottom-up TAM/SAM/SOM model.", "Improve LTV:CAC toward 3x or higher."],
    },
}
mandate = {
    "extracted": extracted, "gate": {"failed_criteria": ["GST number missing or invalid"]},
    "report": rejected["report"],
}

data, pages = build_memo(accepted)
open("memo_test.pdf", "wb").write(data)
print("memo pages:", pages)
open("diagnostic_test.pdf", "wb").write(diagnostic_pdf(rejected))
open("diagnostic_mandate_test.pdf", "wb").write(diagnostic_pdf(mandate))
print("done")
