from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=14)

content = """VentureLens Sample Pitch Deck

Startup Name: EcoCart
Sector: Sustainable E-commerce

Problem Statement:
Small retailers lack affordable tools to track and reduce packaging waste.

Solution:
EcoCart provides a plug-in analytics dashboard that helps online stores
switch to sustainable packaging and track carbon footprint per order.

Market Size:
TAM: $12 Billion (global sustainable packaging market)
SAM: $2 Billion (India + SEA e-commerce packaging)
SOM: $50 Million (achievable in 3 years)

Financials:
Revenue: INR 18 Lakhs (last 12 months)
CAC: INR 450 per customer
LTV: INR 3,200 per customer
Burn Rate: INR 2 Lakhs per month

Traction:
Customers: 340 paying merchants
MRR: INR 1.5 Lakhs
Growth Rate: 22% month-over-month

Team:
Founded by two IIT graduates with prior experience in supply chain 
and sustainability consulting.
"""

for line in content.split("\\n"):
    pdf.cell(0, 8, text=line, new_x="LMARGIN", new_y="NEXT")

pdf.output("sample_data/dummy_pitch_deck.pdf")
print("Dummy pitch deck created at sample_data/dummy_pitch_deck.pdf")
