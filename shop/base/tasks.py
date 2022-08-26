from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from Qaryb_API.celery_conf import app
from celery.utils.log import get_task_logger
from shop.models import AuthShop, TempShop, ModeVacance
from offers.base.tasks import start_generating_thumbnail
from offers.models import TempOffers
from os import path
from account.models import CustomUser
from os import remove


logger = get_task_logger(__name__)
parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))


@app.task(bind=True)
def base_generate_avatar_thumbnail(self, object_pk, which):
    if which == 'AuthShop':
        object_ = AuthShop.objects.get(pk=object_pk)
    elif which == 'CustomUser':
        object_ = CustomUser.objects.get(pk=object_pk)
    else:
        # TempShop
        object_ = TempShop.objects.get(pk=object_pk)
    shop_avatar = object_.avatar.url if object_.avatar else None
    if shop_avatar is not None:
        avatar_path = parent_file_dir + '/media' + object_.avatar.url
        avatar_thumbnail = start_generating_thumbnail(avatar_path, False)
        object_.save_image('avatar_thumbnail', avatar_thumbnail)
        if which == 'AuthShop':
            event = {
                "type": "recieve_group_message",
                "message": {
                    "type": "SHOP_AVATAR",
                    "pk": object_.user.pk,
                    "avatar_thumbnail": object_.get_absolute_avatar_thumbnail,
                }
            }
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)("%s" % object_.user.pk, event)
        elif which == 'CustomUser':
            event = {
                "type": "recieve_group_message",
                "message": {
                    "type": "USER_AVATAR",
                    "pk": object_.pk,
                    "avatar_thumbnail": object_.get_absolute_avatar_thumbnail,
                }
            }
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)("%s" % object_.pk, event)
        else:
            # No event for TempShop user is not known yet.
            pass


@app.task(bind=True)
def base_delete_mode_vacance_obj(self, auth_shop_pk):
    try:
        ModeVacance.objects.get(auth_shop=auth_shop_pk).delete()
    except ModeVacance.DoesNotExist:
        pass


@app.task(bind=True)
def base_start_deleting_expired_shops(self, shop_pk):
    shop = TempShop.objects.get(pk=shop_pk)
    if shop.unique_id is not None:
        # Delete avatar image
        try:
            avatar_img = shop.avatar.path
            remove(avatar_img)
        except (FileNotFoundError, ValueError, AttributeError):
            pass
        # Delete avatar thumbnail
        try:
            avatar_thumbnail_img = shop.avatar_thumbnail.path
            remove(avatar_thumbnail_img)
        except (FileNotFoundError, ValueError, AttributeError):
            pass
        # Delete temp product images
        products = TempOffers.objects.filter(auth_shop=shop.pk)
        for product in products:
            # Picture 1
            try:
                picture_1 = product.picture_1.path
                remove(picture_1)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 1 thumbnail
            try:
                picture_1_thumbnail = product.picture_1_thumbnail.path
                remove(picture_1_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 2
            try:
                picture_2 = product.picture_2.path
                remove(picture_2)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 2 thumbnail
            try:
                picture_2_thumbnail = product.picture_2_thumbnail.path
                remove(picture_2_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 3
            try:
                picture_3 = product.picture_3.path
                remove(picture_3)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 3 thumbnail
            try:
                picture_3_thumbnail = product.picture_3_thumbnail.path
                remove(picture_3_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
        # Delete object
        shop.delete()
