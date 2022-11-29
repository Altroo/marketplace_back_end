import pdfkit


def test_generate_pdf():
    pdfkit.from_file('/Users/youness/Desktop/Qaryb_API/tests/facture.html', '/Users/youness/Desktop/Qaryb_API/tests/out.pdf')


if __name__ == '__main__':
    test_generate_pdf()
