from fpdf import FPDF


def make_pdf(path, sections):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for heading, lines in sections:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.multi_cell(0, 10, heading, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 12)
        for line in lines:
            pdf.multi_cell(0, 8, "- " + line, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
    pdf.output(path)


make_pdf("sample_data/weak_pitch_deck.pdf", [
    ("QuickBite - Food Delivery for Everyone", [
        "Startup: QuickBite Foods Pvt Ltd",
        "Sector: Food delivery",
        "Founder: Rohan Verma, final-year student",
    ]),
    ("Problem and Solution", [
        "Problem: people want food delivered fast.",
        "Solution: a mobile app that delivers food from restaurants to customers.",
    ]),
    ("Market Size", [
        "TAM: the global food industry, over USD 8 Trillion.",
        "SAM: not disclosed.",
        "SOM: not disclosed.",
    ]),
    ("Financials", [
        "Revenue: INR 40,000 in the last 12 months.",
        "CAC: INR 900 per customer. LTV: INR 1,080 per customer. LTV to CAC ratio: 1.2x.",
        "Burn rate: INR 4 Lakhs per month. Cash in bank: INR 3 Lakhs.",
    ]),
    ("Traction", [
        "No paying customers yet; 200 people downloaded the beta app.",
        "No revenue growth data available.",
    ]),
    ("Competition", [
        "Competitors include Swiggy and Zomato. We will compete on being better.",
        "No patents, proprietary technology or exclusive partnerships.",
    ]),
])

make_pdf("sample_data/weak_gst_document.pdf", [
    ("GST Registration Certificate", [
        "Legal Name: QuickBite Foods Private Limited",
        "GSTIN: 07AABCQ9876M1Z3",
        "Date of Registration: 21/08/2025",
        "Status: Active",
    ]),
])
print("created weak sample")
