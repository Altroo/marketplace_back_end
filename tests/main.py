from random import shuffle
import qrcode
from PIL import Image, ImageDraw, ImageFont
import qrcode.image.svg
from cv2 import imread, resize, INTER_AREA, cvtColor, COLOR_BGR2RGB
from io import BytesIO
import textwrap
import random
import re


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
    max_w, max_h = 300, 50
    color_box = Image.new("RGB", (max_w, max_h), color='white')
    # check the length of the text
    # if more than some characters
    # fit the drawn_text_img pixels
    drawn_text_img = ImageDraw.Draw(color_box)
    drawn_text_img.rounded_rectangle(((0, 0), (max_w, max_h)), 20, fill=color)
    # Wrap the text if it's long
    # Limit 40 chars
    astr = "أسرع وأجدد hello"
    words = astr.split()
    my_dict = {}
    for word in words:
        result = latin_or_arabic(word)
        my_dict[word] = result
    for k, v in my_dict.items():
        if v == 'ar':
            font = ImageFont.truetype("/Users/youness/Desktop/Qaryb_API_new/static/fonts/NotoSans-Medium.otf", 16,
                                      encoding='utf-8')
        else:
            font = ImageFont.truetype("/Users/youness/Desktop/test_qr_code/fonts/Poppins-Bold.ttf", 16,
                                      encoding="utf-8")
        para = textwrap.wrap(k, width=20)
        para = '\n'.join(para)
        # draw the wraped text box with the font
        text_width, text_height = drawn_text_img.textsize(para, font=font)
        current_h = 3
        if v == 'ar':
            drawn_text_img.text(((max_w - text_width) / 2, current_h), para, font=font,
                                fill=(255, 255, 255), features='aalt', align='center', language='ar', direction='rtl',
                                layout_engine=ImageFont.Layout.RAQM)
        else:
            drawn_text_img.text(((max_w - text_width) / 2, current_h), para, font=font,
                                fill=(255, 255, 255), align='center')
        qr_img.paste(drawn_text_img._image, (100, 420))
    qr_img.save('gfg_QR.png')
    qr_img.show()


if __name__ == '__main__':
    text = "أسرع وأجدد hello"
    # latin_from_arabic(text)
    generate_qr_code()
