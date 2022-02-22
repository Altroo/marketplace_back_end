from os import path
from Qaryb_API_new.celery_conf import app
from celery.utils.log import get_task_logger
from temp_offer.base.models import TempOffers
from cv2 import imread, resize, INTER_AREA, cvtColor, COLOR_BGR2RGB
from PIL import Image
from io import BytesIO


logger = get_task_logger(__name__)
parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))


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


def from_img_to_io(image, format_):
    image = Image.fromarray(image)
    bytes_io = BytesIO()
    image.save(bytes_io, format=format_)
    bytes_io.seek(0)
    return bytes_io


def start_generating_thumbnail(img_path, duplicate):
    loaded_img = load_image(img_path)
    if duplicate:
        resized_thumb = image_resize(loaded_img)
    else:
        resized_thumb = image_resize(loaded_img, width=300, height=300)
    img_thumbnail = from_img_to_io(resized_thumb, 'PNG')
    return img_thumbnail


@app.task(bind=True)
def base_generate_offer_thumbnails(self, product_id):
    temp_offer = TempOffers.objects.get(pk=product_id)
    temp_offer_picture_1 = temp_offer.picture_1.url if temp_offer.picture_1 else None
    if temp_offer_picture_1 is not None:
        picture_path = parent_file_dir + '/media' + temp_offer.picture_1.url
        img_thumbnail = start_generating_thumbnail(picture_path, False)
        temp_offer.save_image('picture_1_thumbnail', img_thumbnail)

    temp_offer_picture_2 = temp_offer.picture_2.path if temp_offer.picture_2 else None
    if temp_offer_picture_2 is not None:
        picture_path = parent_file_dir + '/media' + temp_offer.picture_2.url
        img_thumbnail = start_generating_thumbnail(picture_path, False)
        temp_offer.save_image('picture_2_thumbnail', img_thumbnail)

    temp_offer_picture_3 = temp_offer.picture_3.path if temp_offer.picture_3 else None
    if temp_offer_picture_3 is not None:
        picture_path = parent_file_dir + '/media' + temp_offer.picture_3.url
        img_thumbnail = start_generating_thumbnail(picture_path, False)
        temp_offer.save_image('picture_3_thumbnail', img_thumbnail)

    temp_offer_picture_4 = temp_offer.picture_4.path if temp_offer.picture_4 else None
    if temp_offer_picture_4 is not None:
        picture_path = parent_file_dir + '/media' + temp_offer.picture_4.url
        img_thumbnail = start_generating_thumbnail(picture_path, False)
        temp_offer.save_image('picture_4_thumbnail', img_thumbnail)


@app.task(bind=True)
def base_duplicate_offer_images(self, offer_id, new_offer_id):
    temp_offer = TempOffers.objects.get(pk=offer_id)
    new_temp_offer = TempOffers.objects.get(pk=new_offer_id)
    if temp_offer.picture_1:
        picture_1 = start_generating_thumbnail(temp_offer.picture_1.path, True)
        new_temp_offer.save_image('picture_1', picture_1)
    if temp_offer.picture_1_thumbnail:
        picture_1_thumbnail = start_generating_thumbnail(temp_offer.picture_1_thumbnail.path, True)
        new_temp_offer.save_image('picture_1_thumbnail', picture_1_thumbnail)
    if temp_offer.picture_2:
        picture_2 = start_generating_thumbnail(temp_offer.picture_2.path, True)
        new_temp_offer.save_image('picture_2', picture_2)
    if temp_offer.picture_2_thumbnail:
        picture_2_thumbnail = start_generating_thumbnail(temp_offer.picture_2_thumbnail.path, True)
        new_temp_offer.save_image('picture_2_thumbnail', picture_2_thumbnail)
    if temp_offer.picture_3:
        picture_3 = start_generating_thumbnail(temp_offer.picture_3.path, True)
        new_temp_offer.save_image('picture_3', picture_3)
    if temp_offer.picture_3_thumbnail:
        picture_3_thumbnail = start_generating_thumbnail(temp_offer.picture_3_thumbnail.path, True)
        new_temp_offer.save_image('picture_3_thumbnail', picture_3_thumbnail)
    if temp_offer.picture_4:
        picture_4 = start_generating_thumbnail(temp_offer.picture_4.path, True)
        new_temp_offer.save_image('picture_4', picture_4)
    if temp_offer.picture_4_thumbnail:
        picture_4_thumbnail = start_generating_thumbnail(temp_offer.picture_4_thumbnail.path, True)
        new_temp_offer.save_image('picture_4_thumbnail', picture_4_thumbnail)

