from io import BytesIO
from os import path, remove
from typing import Tuple
from django.core.exceptions import SuspiciousFileOperation
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from Qaryb_API.celery_conf import app
from celery.utils.log import get_task_logger
from offers.models import Offers, OfferVue
from shop.models import ModeVacance
from shop.base.utils import ImageProcessor

logger = get_task_logger(__name__)
parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))


def start_generating_thumbnail(img_path, duplicate):
    image_processor = ImageProcessor()
    loaded_img = image_processor.load_image(img_path)
    if duplicate:
        resized_thumb = image_processor.image_resize(loaded_img)
    else:
        resized_thumb = image_processor.image_resize(loaded_img, width=300, height=300)
    img_thumbnail = image_processor.from_img_to_io(resized_thumb, 'WEBP')
    return img_thumbnail


def resize_images(img_path):
    image_processor = ImageProcessor()
    loaded_img = image_processor.load_image(img_path)
    resized_img = image_processor.image_resize(loaded_img)
    img = image_processor.from_img_to_io(resized_img, 'WEBP')
    return img


@app.task(bind=True, serializer='json')
def base_generate_offer_thumbnails(self, product_pk):
    offer = Offers.objects.get(pk=product_pk)
    offer_picture_1 = offer.picture_1.url if offer.picture_1 else None
    if offer_picture_1 is not None:
        picture_path = parent_file_dir + '/media' + offer.picture_1.url
        img_thumbnail = start_generating_thumbnail(picture_path, False)
        img = resize_images(picture_path)
        offer.save_image('picture_1_thumbnail', img_thumbnail)
        offer.save_image('picture_1', img)
        # Send offer images (generated offer image)
        event = {
            "type": "recieve_group_message",
            "message": {
                "type": "OFFER_THUMBNAIL",
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
        img = resize_images(picture_path)
        offer.save_image('picture_2_thumbnail', img_thumbnail)
        offer.save_image('picture_2', img)

    offer_picture_3 = offer.picture_3.path if offer.picture_3 else None
    if offer_picture_3 is not None:
        picture_path = parent_file_dir + '/media' + offer.picture_3.url
        img_thumbnail = start_generating_thumbnail(picture_path, False)
        img = resize_images(picture_path)
        offer.save_image('picture_3_thumbnail', img_thumbnail)
        offer.save_image('picture_3', img)

    offer_picture_4 = offer.picture_4.path if offer.picture_4 else None
    if offer_picture_4 is not None:
        picture_path = parent_file_dir + '/media' + offer.picture_4.url
        img_thumbnail = start_generating_thumbnail(picture_path, False)
        img = resize_images(picture_path)
        offer.save_image('picture_4_thumbnail', img_thumbnail)
        offer.save_image('picture_4', img)


@app.task(bind=True, serializer='json')
def base_duplicate_offer_images(self, offer_pk, new_offer_pk):
    offer = Offers.objects.get(pk=offer_pk)
    new_offer = Offers.objects.get(pk=new_offer_pk)
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
                "type": "OFFER_THUMBNAIL",
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
    if offer.picture_4_thumbnail:
        picture_4_thumbnail = start_generating_thumbnail(offer.picture_4_thumbnail.path, True)
        new_offer.save_image('picture_4_thumbnail', picture_4_thumbnail)


def resize_images_v2(bytes_) -> Tuple[BytesIO, BytesIO]:
    image_processor = ImageProcessor()
    loaded_img = image_processor.load_image_from_io(bytes_)
    resized_img = image_processor.image_resize(loaded_img)
    resized_thumb = image_processor.image_resize(loaded_img, width=300, height=300)
    img = image_processor.from_img_to_io(resized_img, 'WEBP')
    thumb = image_processor.from_img_to_io(resized_thumb, 'WEBP')
    return img, thumb


def send_ws_image(user_pk: int, offer_pk: int, url: str, type_: str):
    event = {
        "type": "recieve_group_message",
        "message": {
            "type": type_,
            "pk": offer_pk,
            "offer_picture": url,
        }
    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)("%s" % user_pk, event)


def generate_images_v2(query_, picture: BytesIO, picture_name: str):
    img, thumb = resize_images_v2(picture)
    query_.save_image(picture_name, img)
    query_.save_image('{}_thumbnail'.format(picture_name), thumb)
    if picture_name != 'avatar':
        user_pk = query_.auth_shop.user.pk
        query_pk = query_.pk
        match picture_name:
            case 'picture_1':
                send_ws_image(user_pk, query_pk, query_.get_absolute_picture_1_img, 'OFFER_PICTURE_1')
                send_ws_image(user_pk, query_pk, query_.get_absolute_picture_1_thumbnail, 'OFFER_PICTURE_1_THUMB')
            case 'picture_2':
                send_ws_image(user_pk, query_pk, query_.get_absolute_picture_2_img, 'OFFER_PICTURE_2')
                send_ws_image(user_pk, query_pk, query_.get_absolute_picture_2_thumbnail, 'OFFER_PICTURE_2_THUMB')
            case 'picture_3':
                send_ws_image(user_pk, query_pk, query_.get_absolute_picture_3_img, 'OFFER_PICTURE_3')
                send_ws_image(user_pk, query_pk, query_.get_absolute_picture_3_thumbnail, 'OFFER_PICTURE_3_THUMB')
            case 'picture_4':
                send_ws_image(user_pk, query_pk, query_.get_absolute_picture_4_img, 'OFFER_PICTURE_4')
                send_ws_image(user_pk, query_pk, query_.get_absolute_picture_4_thumbnail, 'OFFER_PICTURE_4_THUMB')

# @app.task(bind=True)
# def base_resize_offer_images(self, offer_pk: int,
#                              picture_1: str | None,
#                              picture_2: str | None,
#                              picture_3: str | None,
#                              picture_4: str | None):
#     offer = Offers.objects.get(pk=offer_pk)
#     if isinstance(picture_1, str):
#         generate_images_v2(offer, BytesIO(bytes(picture_1)), 'picture_1')
#     if isinstance(picture_2, str):
#         generate_images_v2(offer, BytesIO(bytes(picture_2)), 'picture_2')
#     if isinstance(picture_3, str):
#         generate_images_v2(offer, BytesIO(bytes(picture_3)), 'picture_3')
#     if isinstance(picture_4, str):
#         generate_images_v2(offer, BytesIO(bytes(picture_4)), 'picture_4')


@app.task(bind=True, serializer='pickle')
def base_resize_offer_images(self, offer_pk: int,
                             picture_1: BytesIO | None,
                             picture_2: BytesIO | None,
                             picture_3: BytesIO | None,
                             picture_4: BytesIO | None):
    offer = Offers.objects.get(pk=offer_pk)
    if isinstance(picture_1, BytesIO):
        generate_images_v2(offer, picture_1, 'picture_1')
    if isinstance(picture_2, BytesIO):
        generate_images_v2(offer, picture_2, 'picture_2')
    if isinstance(picture_3, BytesIO):
        generate_images_v2(offer, picture_3, 'picture_3')
    if isinstance(picture_4, BytesIO):
        generate_images_v2(offer, picture_4, 'picture_4')


@app.task(bind=True, serializer='json')
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
        if offer.picture_4:
            picture_4 = start_generating_thumbnail(offer.picture_4.path, True)
            offer_vue.save_image('thumbnail', picture_4)
            break
        if offer.picture_4_thumbnail:
            picture_4_thumbnail = start_generating_thumbnail(offer.picture_4_thumbnail.path, True)
            offer_vue.save_image('thumbnail', picture_4_thumbnail)
            break


# @app.task(bind=True, serializer='json')
# def base_generate_avatar_thumbnail(self, object_pk, which):
#     if which == 'AuthShop':
#         object_ = AuthShop.objects.get(pk=object_pk)
#     else:
#         object_ = CustomUser.objects.get(pk=object_pk)
#     shop_avatar = object_.avatar.url if object_.avatar else None
#     if shop_avatar is not None:
#         avatar_path = parent_file_dir + '/media' + object_.avatar.url
#         avatar_thumbnail = start_generating_thumbnail(avatar_path, False)
#         avatar = resize_images(avatar_path)
#         object_.save_image('avatar_thumbnail', avatar_thumbnail)
#         object_.save_image('avatar', avatar)
#         if which == 'AuthShop':
#             event = {
#                 "type": "recieve_group_message",
#                 "message": {
#                     "type": "SHOP_AVATAR",
#                     "pk": object_.user.pk,
#                     "avatar_thumbnail": object_.get_absolute_avatar_thumbnail,
#                 }
#             }
#             channel_layer = get_channel_layer()
#             async_to_sync(channel_layer.group_send)("%s" % object_.user.pk, event)
#         elif which == 'CustomUser':
#             event = {
#                 "type": "recieve_group_message",
#                 "message": {
#                     "type": "USER_AVATAR",
#                     "pk": object_.pk,
#                     "avatar_thumbnail": object_.get_absolute_avatar_thumbnail,
#                 }
#             }
#             channel_layer = get_channel_layer()
#             async_to_sync(channel_layer.group_send)("%s" % object_.pk, event)
#         else:
#             # No event for TempShop user is not known yet.
#             pass


@app.task(bind=True, serializer='json')
def base_delete_mode_vacance_obj(self, auth_shop_pk):
    try:
        ModeVacance.objects.get(auth_shop=auth_shop_pk).delete()
    except ModeVacance.DoesNotExist:
        pass


@app.task(bind=True, serializer='json')
def base_delete_shop_media_files(self, media_paths_list):
    for media_path in media_paths_list:
        try:
            remove(media_path)
        except (ValueError, SuspiciousFileOperation, FileNotFoundError):
            pass

# @app.task(bind=True)
# def base_start_deleting_expired_shops(self, shop_pk):
#     auth_shop = TempShop.objects.get(pk=shop_pk)
#     if auth_shop.unique_id is not None:
#         # Delete avatar image
#         try:
#             avatar_img = auth_shop.avatar.path
#             remove(avatar_img)
#         except (FileNotFoundError, ValueError, AttributeError):
#             pass
#         # Delete avatar thumbnail
#         try:
#             avatar_thumbnail_img = auth_shop.avatar_thumbnail.path
#             remove(avatar_thumbnail_img)
#         except (FileNotFoundError, ValueError, AttributeError):
#             pass
#         # Delete temp product images
#         products = TempOffers.objects.filter(auth_shop=auth_shop.pk)
#         for product in products:
#             # Picture 1
#             try:
#                 picture_1 = product.picture_1.path
#                 remove(picture_1)
#             except (FileNotFoundError, ValueError, AttributeError):
#                 pass
#             # Picture 1 thumbnail
#             try:
#                 picture_1_thumbnail = product.picture_1_thumbnail.path
#                 remove(picture_1_thumbnail)
#             except (FileNotFoundError, ValueError, AttributeError):
#                 pass
#             # Picture 2
#             try:
#                 picture_2 = product.picture_2.path
#                 remove(picture_2)
#             except (FileNotFoundError, ValueError, AttributeError):
#                 pass
#             # Picture 2 thumbnail
#             try:
#                 picture_2_thumbnail = product.picture_2_thumbnail.path
#                 remove(picture_2_thumbnail)
#             except (FileNotFoundError, ValueError, AttributeError):
#                 pass
#             # Picture 3
#             try:
#                 picture_3 = product.picture_3.path
#                 remove(picture_3)
#             except (FileNotFoundError, ValueError, AttributeError):
#                 pass
#             # Picture 3 thumbnail
#             try:
#                 picture_3_thumbnail = product.picture_3_thumbnail.path
#                 remove(picture_3_thumbnail)
#             except (FileNotFoundError, ValueError, AttributeError):
#                 pass
#             # Picture 4
#             try:
#                 picture_4 = product.picture_4.path
#                 remove(picture_4)
#             except (FileNotFoundError, ValueError, AttributeError):
#                 pass
#             # Picture 4 thumbnail
#             try:
#                 picture_4_thumbnail = product.picture_4_thumbnail.path
#                 remove(picture_4_thumbnail)
#             except (FileNotFoundError, ValueError, AttributeError):
#                 pass
#         # Delete object
#         auth_shop.delete()
