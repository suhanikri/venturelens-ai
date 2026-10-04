from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", "B", 14)
pdf.cell(0, 10, "GST Registration Certificate", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 11)
for line in ["Legal Name: EcoCart Private Limited",
             "GSTIN: 99XXXXX0000X0X0",
             "Date of Registration: 14/03/2023",
             "Status: Cancelled"]:
    pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
pdf.output("sample_data/bad_gst_document.pdf")
print("created")
