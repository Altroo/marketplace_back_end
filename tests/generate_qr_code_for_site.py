import qrcode


def generate_qr_code_v2():
    qr_code = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=20,
        border=1,
    )
    # qr_code.add_data("https://qaryb.com/boutique-en-ligne-maroc")
    qr_code.add_data("https://qaryb.com/insta")
    qr_code.make(fit=True)
    img = qr_code.make_image(fill_color="black", back_color="white")
    img.save("qr_code.png")


if __name__ == '__main__':
    generate_qr_code_v2()
