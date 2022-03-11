from Qaryb_API_new.celery_conf import app
from celery.utils.log import get_task_logger
from PIL import Image, ImageDraw, ImageFont
from account.models import CustomUser
from Qaryb_API_new.settings import STATIC_PATH
from io import BytesIO
from random import shuffle
from django.core.files import File


logger = get_task_logger(__name__)


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
    bytes_io = BytesIO()
    image.save(File(bytes_io), format=format_, save=False)
    bytes_io.seek(0)
    return bytes_io


def start_generating_avatar_and_thumbnail(last_name, first_name):
    colors = random_color_picker()
    shuffle(colors)
    color = colors.pop()
    avatar = Image.new("RGB", (600, 600), color=color)
    font_avatar = ImageFont.truetype(STATIC_PATH + "/fonts/Poppins-Bold.ttf", 240)
    drawn_avatar = ImageDraw.Draw(avatar)
    drawn_avatar.text((100, 136), "{}.{}".format(first_name, last_name), font=font_avatar, fill=(0, 0, 0))
    thumbnail = Image.new("RGB", (300, 300), color=color)
    font_thumb = ImageFont.truetype(STATIC_PATH + "/fonts/Poppins-Bold.ttf", 120)
    drawn_thumb = ImageDraw.Draw(thumbnail)
    drawn_thumb.text((50, 68), "{}.{}".format(first_name, last_name), font=font_thumb, fill=(0, 0, 0))
    return avatar, thumbnail


@app.task(bind=True)
def base_generate_user_thumbnail(self, user_pk):
    user = CustomUser.objects.get(pk=user_pk)
    last_name = str(user.last_name[0]).upper()
    first_name = str(user.first_name[0]).upper()
    avatar, thumbnail = start_generating_avatar_and_thumbnail(last_name, first_name)
    avatar_ = from_img_to_io(avatar, 'PNG')
    thumbnail_ = from_img_to_io(thumbnail, 'PNG')
    user.save_image('avatar', avatar_)
    user.save_image('avatar_thumbnail', thumbnail_)
