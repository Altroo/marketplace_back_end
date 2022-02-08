from os import path
from Qaryb_API_new.celery_conf import app
from celery.utils.log import get_task_logger
from temp_shop.base.models import TempShop


logger = get_task_logger(__name__)
parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))


@app.task(bind=True)
def base_start_deleting_expired_shops(self, shop_id):
    temp_shop = TempShop.objects.get(pk=shop_id)
    if temp_shop.unique_id is not None:
        TempShop.objects.get(pk=shop_id).delete()
