from os import path
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from Qaryb_API_new.celery_conf import app
from celery.utils.log import get_task_logger
from offer.base.models import Offers, OfferVue
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
def base_generate_offer_thumbnails(self, product_pk, which):
    if which == 'Offers':
        offer = Offers.objects.get(pk=product_pk)
    else:
        offer = TempOffers.objects.get(pk=product_pk)
    offer_picture_1 = offer.picture_1.url if offer.picture_1 else None
    if offer_picture_1 is not None:
        picture_path = parent_file_dir + '/media' + offer.picture_1.url
        img_thumbnail = start_generating_thumbnail(picture_path, False)
        offer.save_image('picture_1_thumbnail', img_thumbnail)
        # Send offer images (generated offer image)
        event = {
            "type": "recieve_group_message",
            "message": {
                "type": "offer_thumbnail",
                "pk": offer.pk,
                "offer_thumbnail": offer.get_absolute_picture_1_thumbnail,
            }
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("%s" % offer.auth_shop.user.pk, event)

    offer_picture_2 = offer.picture_2.path if offer.picture_2 else None
    if offer_picture_2 is not None:
        picture_path = parent_file_dir + '/media' + offer.picture_2.url
        img_thumbnail = start_generating_thumbnail(picture_path, False)
        offer.save_image('picture_2_thumbnail', img_thumbnail)

    offer_picture_3 = offer.picture_3.path if offer.picture_3 else None
    if offer_picture_3 is not None:
        picture_path = parent_file_dir + '/media' + offer.picture_3.url
        img_thumbnail = start_generating_thumbnail(picture_path, False)
        offer.save_image('picture_3_thumbnail', img_thumbnail)


@app.task(bind=True)
def base_duplicate_offer_images(self, offer_pk, new_offer_pk, which):
    if which == 'Offers':
        offer = Offers.objects.get(pk=offer_pk)
        new_offer = Offers.objects.get(pk=new_offer_pk)
    else:
        offer = TempOffers.objects.get(pk=offer_pk)
        new_offer = TempOffers.objects.get(pk=new_offer_pk)

    if offer.picture_1:
        picture_1 = start_generating_thumbnail(offer.picture_1.path, True)
        new_offer.save_image('picture_1', picture_1)
    if offer.picture_1_thumbnail:
        picture_1_thumbnail = start_generating_thumbnail(offer.picture_1_thumbnail.path, True)
        new_offer.save_image('picture_1_thumbnail', picture_1_thumbnail)
        # Send offer images (generated offer image)
        event = {
            "type": "recieve_group_message",
            "message": {
                "type": "offer_thumbnail",
                "pk": new_offer.pk,
                "offer_thumbnail": new_offer.get_absolute_picture_1_thumbnail,
            }
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("%s" % offer.auth_shop.user.pk, event)
    if offer.picture_2:
        picture_2 = start_generating_thumbnail(offer.picture_2.path, True)
        new_offer.save_image('picture_2', picture_2)
    if offer.picture_2_thumbnail:
        picture_2_thumbnail = start_generating_thumbnail(offer.picture_2_thumbnail.path, True)
        new_offer.save_image('picture_2_thumbnail', picture_2_thumbnail)
    if offer.picture_3:
        picture_3 = start_generating_thumbnail(offer.picture_3.path, True)
        new_offer.save_image('picture_3', picture_3)
    if offer.picture_3_thumbnail:
        picture_3_thumbnail = start_generating_thumbnail(offer.picture_3_thumbnail.path, True)
        new_offer.save_image('picture_3_thumbnail', picture_3_thumbnail)


@app.task(bind=True)
def base_duplicate_offervue_images(self, offer_pk):
    offer = Offers.objects.get(pk=offer_pk)
    offer_vue = OfferVue.objects.get(offer=offer_pk)
    while True:
        if offer.picture_1:
            picture_1 = start_generating_thumbnail(offer.picture_1.path, True)
            offer_vue.save_image('thumbnail', picture_1)
            break
        if offer.picture_2:
            picture_2 = start_generating_thumbnail(offer.picture_2.path, True)
            offer_vue.save_image('thumbnail', picture_2)
            break
        if offer.picture_2_thumbnail:
            picture_2_thumbnail = start_generating_thumbnail(offer.picture_2_thumbnail.path, True)
            offer_vue.save_image('thumbnail', picture_2_thumbnail)
            break
        if offer.picture_3:
            picture_3 = start_generating_thumbnail(offer.picture_3.path, True)
            offer_vue.save_image('thumbnail', picture_3)
            break
        if offer.picture_3_thumbnail:
            picture_3_thumbnail = start_generating_thumbnail(offer.picture_3_thumbnail.path, True)
            offer_vue.save_image('thumbnail', picture_3_thumbnail)
            break
