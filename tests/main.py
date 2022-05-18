from random import shuffle
import qrcode
from PIL import Image, ImageDraw, ImageFont
import qrcode.image.svg
from cv2 import imread, resize, INTER_AREA, cvtColor, COLOR_BGR2RGB
from io import BytesIO
import textwrap
import random
import re
import arabic_reshaper
from bidi.algorithm import get_display


# import requests


def load_image(img_path):
    loaded_img = cvtColor(imread(img_path), COLOR_BGR2RGB)
    return loaded_img


def image_resize(image, width=None, height=None, inter=INTER_AREA):
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image

    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)

    else:
        r = width / float(w)
        dim = (width, int(h * r))

    resized = resize(image, dim, interpolation=inter)
    return resized


def random_color_picker():
    colors = [
        # Red
        (255, 93, 107),
        # Orange
        (255, 168, 38),
        # Yellow
        (254, 211, 1),
        # Green
        (7, 203, 173),
        # Blue
        (2, 116, 215),
        # Purple
        (134, 105, 251),
        # Pink
        (255, 157, 191),
        # Brown
        (206, 177, 134)
    ]
    return colors


def from_img_to_io(image, format_):
    image = Image.fromarray(image)
    bytes_io = BytesIO()
    image.save(bytes_io, format=format_)
    bytes_io.seek(0)
    return bytes_io


def latin_or_arabic(word):
    arabic = 'ar'
    latin = 'la'
    arabic_unicode_range = r'[\u0600-\u06ff]'
    if re.search(arabic_unicode_range, word):
        return arabic
    return latin


def generate_qr_code():
    img_path = '/Users/youness/Desktop/Qaryb_API_new/static/icons/qaryb_icon_300_300.png'
    loaded_img = load_image(img_path)
    resized_img = image_resize(loaded_img, width=1000, height=1000)
    img_thumbnail = from_img_to_io(resized_img, 'PNG')
    logo = Image.open(img_thumbnail)
    # logo.show()
    basewidth = 100
    # adjust image size
    wpercent = (basewidth / float(logo.size[0]))
    hsize = int((float(logo.size[1]) * float(wpercent)))
    logo = logo.resize((basewidth, hsize), Image.Resampling.LANCZOS)
    qr_code = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=10,
    )
    # taking url or text
    url = 'https://www.qaryb.com'
    # adding URL or text to QRcode
    qr_code.add_data(url)
    # generating QR code
    qr_code.make(fit=True)
    # taking color name from user
    qr_color = 'Black'
    # adding color to QR code
    qr_img = qr_code.make_image(fill_color=qr_color, back_color="white").convert('RGBA')
    # set size of QR code
    pos = ((qr_img.size[0] - logo.size[0]) // 2,
           (qr_img.size[1] - logo.size[1]) // 2)
    qr_img.paste(logo, pos)
    colors = random_color_picker()
    shuffle(colors)
    color = colors.pop()
    max_w, max_h = 300, 60
    color_box = Image.new("RGB", (max_w, max_h), color='white')
    drawn_text_img = ImageDraw.Draw(color_box)
    drawn_text_img.rounded_rectangle(((0, 0), (max_w, max_h)), 20, fill=color)
    # Limit 40 chars
    unicode_text = "بِسم اللَه I'm currently (test) on Windows UVWXYZ UVWXYZ UVWXYZ"
    # unicode_text = "اللَه بِسم اللَه بِسم اللَه بِسم اللَه"
    # unicode_text = "ABCD EFGH IJKL MNOPT QRST UVWXYZ IJKLMNO IJKLMNO IJKLMNO IJKLMNO"
    unicode_text_reshaped = arabic_reshaper.reshape(unicode_text)
    para = textwrap.wrap(unicode_text_reshaped, width=35)
    para = '\n'.join(para)
    unicode_text_reshaped_rtl = get_display(para, base_dir='R')
    unicode_font = ImageFont.truetype("/Users/youness/Desktop/Qaryb_API_new/static/fonts/Changa-Regular.ttf", 16)
    current_h = 3
    text_width, text_height = drawn_text_img.textsize(unicode_text_reshaped_rtl, font=unicode_font)
    drawn_text_img.text(((max_w - text_width) / 2, current_h), unicode_text_reshaped_rtl, align='center', font=unicode_font,
                        fill=(0, 0, 0))
    qr_img.paste(drawn_text_img._image, (100, 420))
    # print(str(qr_img))
    qr_img.save('gfg_QR.png')
    qr_img.show()


def test():
    # configuration
    width = 200
    height = 100
    back_ground_color = (255, 255, 255)
    font_size = 36
    font_color = (0, 0, 0)

    unicode_text = u"Hello بِسم اللَه ABCDEFGHIJK"
    # unicode_text = u"Hello"
    unicode_text_reshaped = arabic_reshaper.reshape(unicode_text)
    unicode_text_reshaped_rtl = get_display(unicode_text_reshaped, base_dir='R')
    im = Image.new("RGB", (width, height), back_ground_color)
    draw = ImageDraw.Draw(im)
    unicode_font = ImageFont.truetype("/Users/youness/Desktop/Qaryb_API_new/static/fonts/Changa-Regular.ttf",
                                      font_size)
    draw.text((10, 10), unicode_text_reshaped_rtl, font=unicode_font, fill=font_color)

    im.save("text.png")
    im.show()


if __name__ == '__main__':
    text = "أسرع وأجدد hello"
    # latin_from_arabic(text)
    generate_qr_code()
    # test()
