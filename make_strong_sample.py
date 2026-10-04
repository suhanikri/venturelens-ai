from fpdf import FPDF


def make_pdf(path, title, sections):
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


make_pdf("sample_data/strong_pitch_deck.pdf", "FleetSense", [
    ("FleetSense - Fleet Intelligence for Indian Logistics", [
        "Startup: FleetSense Technologies Pvt Ltd",
        "Sector: Logistics SaaS / Fleet Analytics",
        "Founders: Ananya Rao (CEO, 9 years running fleet operations) and Karthik Menon (CTO, 11 years building telematics platforms)",
    ]),
    ("Problem and Solution", [
        "Problem: mid-size fleet operators lose 12 to 18 percent of fuel and idle-time cost because they cannot see driver and vehicle performance in real time.",
        "Solution: FleetSense is a SaaS platform that reads telematics data from any vehicle and shows fuel waste, route deviation, and maintenance risk, with automated alerts.",
        "Customers pay an annual subscription per vehicle; average contract is 3 years.",
    ]),
    ("Market Size (bottom-up)", [
        "TAM: USD 3.6 Billion. 4.2 million commercial trucks in India x USD 850 annual software spend per vehicle.",
        "SAM: USD 640 Million. 750,000 trucks owned by fleets of 20 or more vehicles (our target segment) x USD 850.",
        "SOM: USD 32 Million within 3 years. 5 percent of SAM, 37,500 vehicles, based on our current sales pipeline and a 14-person sales team.",
        "Pricing: USD 850 per vehicle per year, validated across 128 paying customers.",
    ]),
    ("Financials", [
        "Revenue: INR 6.1 Crore in the last 12 months. Current MRR: INR 58 Lakhs.",
        "Gross margin: 79 percent.",
        "CAC: INR 42,000 per customer. LTV: INR 4,60,000 per customer. LTV to CAC ratio: 10.9x. CAC payback: 5 months.",
        "Burn rate: INR 7 Lakhs per month. Cash in bank: INR 2.1 Crore. Runway: 30 months. Monthly burn is well below monthly revenue.",
    ]),
    ("Traction", [
        "128 paying fleet customers managing 41,000 vehicles.",
        "Month-over-month revenue growth: 12 percent for the last 10 months.",
        "Net revenue retention: 121 percent. Monthly logo churn: 0.8 percent.",
        "Three public-sector logistics contracts signed on 3-year terms.",
    ]),
    ("Competitive Moat", [
        "Proprietary dataset of 1.4 billion kilometres of Indian road and driver telemetry, which improves our fuel-waste model with every customer.",
        "2 patents filed on our fuel-waste detection algorithm, 1 patent granted.",
        "Deep integrations with 14 vehicle manufacturers and 6 ERP systems; customers average 9 months to migrate away.",
        "Network effect: benchmarking across customers is only possible on our platform.",
    ]),
    ("Team", [
        "Ananya Rao, CEO: ran a 2,000-vehicle fleet for 9 years.",
        "Karthik Menon, CTO: built telematics products at two listed technology companies.",
        "Team of 46 people: 22 engineering, 14 sales, 6 customer success, 4 operations.",
    ]),
])

make_pdf("sample_data/strong_gst_document.pdf", "GST", [
    ("GST Registration Certificate", [
        "Legal Name: FleetSense Technologies Private Limited",
        "GSTIN: 29AABCF4821K1Z5",
        "Date of Registration: 02/06/2021",
        "Status: Active",
        "State: Karnataka",
    ]),
])
print("created strong_pitch_deck.pdf and strong_gst_document.pdf")
