from fpdf import FPDF


def base_generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.image('/Users/youness/Desktop/Qaryb_API/static/icons/pdf_template.png', x=None, y=None)
    pdf.close()
    pdf.output('/Users/youness/Desktop/Qaryb_API/tests/a.pdf')
    # https://www.geeksforgeeks.org/python-convert-html-pdf/
    # https://stackoverflow.com/questions/23359083/how-to-convert-webpage-into-pdf-by-using-python


if __name__ == '__main__':
    base_generate_pdf()
