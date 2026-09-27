from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=14)

content = """GOODS AND SERVICES TAX CERTIFICATE
(Sample/Dummy Document for Testing)

Legal Name of Business: EcoCart Technologies Private Limited
GSTIN: 27AABCE1234F1Z5
Date of Registration: 14/03/2023
Constitution of Business: Private Limited Company
Status: Active

This is a dummy GST certificate generated for testing purposes only.
"""

for line in content.split("\\n"):
    pdf.cell(0, 8, text=line, new_x="LMARGIN", new_y="NEXT")

pdf.output("sample_data/dummy_gst_document.pdf")
print("Dummy GST document created at sample_data/dummy_gst_document.pdf")
