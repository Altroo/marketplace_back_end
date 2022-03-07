from Qaryb_API_new.celery_conf import app
from celery.utils.log import get_task_logger
from auth_shop.base.models import AuthShop
from offer.base.tasks import start_generating_thumbnail
from os import path
from temp_shop.base.models import TempShop

logger = get_task_logger(__name__)
parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))


@app.task(bind=True)
def base_generate_avatar_thumbnail(self, shop_id, which):
    if which == 'AuthShop':
        auth_shop = AuthShop.objects.get(pk=shop_id)
    else:
        auth_shop = TempShop.objects.get(pk=shop_id)
    shop_avatar = auth_shop.avatar.url if auth_shop.avatar else None
    if shop_avatar is not None:
        avatar_path = parent_file_dir + '/media' + auth_shop.avatar.url
        avatar_thumbnail = start_generating_thumbnail(avatar_path, False)
        auth_shop.save_image('avatar_thumbnail', avatar_thumbnail)
