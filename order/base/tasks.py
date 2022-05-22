from os import path
from Qaryb_API_new.celery_conf import app
from celery.utils.log import get_task_logger
from account.models import CustomUser
from shop.base.models import AuthShop
from order.base.models import Order, OrderDetails
from offers.base.models import Offers
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
