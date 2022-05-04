from random import shuffle

import qrcode
from PIL import Image, ImageDraw, ImageFont
import qrcode.image.svg
from cv2 import imread, resize, INTER_AREA, cvtColor, COLOR_BGR2RGB
from io import BytesIO


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
    qr_img.save('gfg_QR.png')
    colors = random_color_picker()
    shuffle(colors)
    color = colors.pop()
    color_box = Image.new("RGB", (300, 50), color='white')
    # check the length of the text
    # if more than some characters
    # add two lines rounded fill
    drawn_text_img = ImageDraw.Draw(color_box)
    drawn_text_img.rounded_rectangle(((0, 0), (300, 50)), 20, fill=color)
    font = ImageFont.truetype("/Users/youness/Desktop/Qaryb_API_new/static/fonts/Poppins-Bold.ttf", 16)
    drawn_text_img.text((90, 12), "Scannez-moi bla bla bla bla bla bla!", font=font, fill=(255, 255, 255))
    qr_img.paste(drawn_text_img._image, (100, 420))
    qr_img.show()

    print('QR code generated!')


if __name__ == '__main__':
    generate_qr_code()
