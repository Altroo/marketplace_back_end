from Qaryb_API_new.celery_conf import app
from celery.utils.log import get_task_logger
from temp_shop.base.models import TempShop
from temp_offer.base.models import TempOffers
from temp_offer.base.tasks import start_generating_thumbnail
from os import remove, path


logger = get_task_logger(__name__)
parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))


@app.task(bind=True)
def base_start_deleting_expired_shops(self, shop_id):
    temp_shop = TempShop.objects.get(pk=shop_id)
    if temp_shop.unique_id is not None:
        # Delete avatar image
        try:
            avatar_img = temp_shop.avatar.path
            remove(avatar_img)
        except (FileNotFoundError, ValueError, AttributeError) as err:
            print(err)
        # Delete avatar thumbnail
        try:
            avatar_thumbnail_img = temp_shop.avatar_thumbnail.path
            remove(avatar_thumbnail_img)
        except (FileNotFoundError, ValueError, AttributeError) as err:
            print(err)
        # Delete temp product images
        temp_products = TempOffers.objects.filter(temp_shop=temp_shop.pk)
        for temp_product in temp_products:
            # Picture 1
            try:
                picture_1 = temp_product.picture_1.path
                remove(picture_1)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 1 thumbnail
            try:
                picture_1_thumbnail = temp_product.picture_1_thumbnail.path
                remove(picture_1_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 2
            try:
                picture_2 = temp_product.picture_2.path
                remove(picture_2)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 2 thumbnail
            try:
                picture_2_thumbnail = temp_product.picture_2_thumbnail.path
                remove(picture_2_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 3
            try:
                picture_3 = temp_product.picture_3.path
                remove(picture_3)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 3 thumbnail
            try:
                picture_3_thumbnail = temp_product.picture_3_thumbnail.path
                remove(picture_3_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 4
            try:
                picture_4 = temp_product.picture_4.path
                remove(picture_4)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 4 thumbnail
            try:
                picture_4_thumbnail = temp_product.picture_4_thumbnail.path
                remove(picture_4_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
        # Delete object
        temp_shop.delete()


@app.task(bind=True)
def base_generate_avatar_thumbnail(self, temp_shop_id):
    temp_shop = TempShop.objects.get(pk=temp_shop_id)
    temp_shop_avatar = temp_shop.avatar.url if temp_shop.avatar else None
    if temp_shop_avatar is not None:
        avatar_path = parent_file_dir + '/media' + temp_shop.avatar.url
        avatar_thumbnail = start_generating_thumbnail(avatar_path, False)
        temp_shop.save_image('avatar_thumbnail', avatar_thumbnail)
