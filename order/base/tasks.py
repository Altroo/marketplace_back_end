from os import path
from Qaryb_API.celery_conf import app
from celery.utils.log import get_task_logger
from account.models import CustomUser
from shop.models import AuthShop
from order.models import Order, OrderDetails
from offers.models import Offers
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


@app.task(bind=True)
def base_duplicate_order_images(self, buyer_pk, seller_pk, offer_pk, which):
    if which == 'buyer_avatar_thumbnail':
        buyer = CustomUser.objects.get(pk=buyer_pk)
        order = Order.objects.get(buyer=buyer)
        if buyer.avatar_thumbnail:
            avatar = start_generating_thumbnail(buyer.avatar_thumbnail.path, True)
            order.save_image('buyer_avatar_thumbnail', avatar)
    elif which == 'seller_avatar_thumbnail':
        seller = AuthShop.objects.get(pk=seller_pk)
        order = Order.objects.get(seller=seller)
        if seller.avatar_thumbnail:
            avatar = start_generating_thumbnail(seller.avatar_thumbnail.path, True)
            order.save_image('seller_avatar_thumbnail', avatar)
    # offer_thumbnail
    else:
        offer = Offers.objects.get(pk=offer_pk)
        order_details = OrderDetails.objects.get(pk=offer)
        if offer.picture_1_thumbnail:
            offer_thumbnail = start_generating_thumbnail(offer.picture_1_thumbnail.path, True)
            order_details.save_image('offer_thumbnail', offer_thumbnail)
