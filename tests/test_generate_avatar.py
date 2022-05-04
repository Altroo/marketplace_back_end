import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Qaryb_API_new.settings')
application = get_wsgi_application()

# from Qaryb_API_new.celery_conf import app
from PIL import Image, ImageDraw, ImageFont
# from account.models import CustomUser
from ..Qaryb_API_new.settings import STATIC_PATH


def start_generating_avatar_and_thumbnail(first_name, last_name):
    avatar = Image.new('RGB', (300, 300), color=(13, 7, 11))
    font_ = ImageFont.truetype(STATIC_PATH + '/rest_framework/fonts/fontawesome-webfont.ttf', 120)
    drawn_avatar = ImageDraw.Draw(avatar)
    drawn_avatar.text((66, 80), "{}.{}".format(first_name, last_name), font=font_, fill=(255, 255, 255))
    return avatar


def base_generate_user_thumbnail(user_pk):
    # user = CustomUser.objects.get(pk=user_pk)
    # first_name = user.first_name[0]
    # last_name = user.last_name[0]
    first_name = 'y'
    last_name = 'e'
    avatar = start_generating_avatar_and_thumbnail(first_name, last_name)
    user.save_image('avatar_thumbnail', avatar)


if __name__ == '__main__':
    base_generate_user_thumbnail(3)
