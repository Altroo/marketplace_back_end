from os import path, rename
from uuid import uuid4
from Qaryb_API_new.celery_conf import app
from celery.utils.log import get_task_logger
from Qaryb_API_new.settings import IMAGES_ROOT_NAME, PRODUCT_IMAGES_BASE_NAME
from temp_shop.base.models import TempShop
from temp_product.base.models import TempProduct
from cv2 import imread, resize, INTER_AREA, cvtColor, COLOR_BGR2RGB
from PIL import Image
from io import BytesIO


logger = get_task_logger(__name__)
parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))


@app.task(bind=True)
def base_start_deleting_expired_shops(self, shop_id):
    temp_shop = TempShop.objects.get(pk=shop_id)
    if temp_shop.unique_id is not None:
        TempShop.objects.get(pk=shop_id).delete()


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


def start_generating_thumbnail(img_path):
    loaded_img = load_image(img_path)
    resized_thumb = image_resize(loaded_img, width=300, height=300)
    img_thumbnail = from_img_to_io(resized_thumb, 'PNG')
    return img_thumbnail


# def rename_product_pictures(picture):
#     picture_name, picture_extension = path.splitext(str(picture))
#     picture_id_name = str(uuid4()) + str(picture_extension)
#     try:
#         rename(parent_file_dir + IMAGES_ROOT_NAME + 'media/' +
#                picture_name + picture_extension,
#                parent_file_dir + PRODUCT_IMAGES_BASE_NAME + '/' + picture_id_name)
#     except FileNotFoundError:
#         pass
#     return PRODUCT_IMAGES_BASE_NAME + '/' + picture_id_name


@app.task(bind=True)
def base_generate_product_thumbnails(self, product_id):
    temp_product = TempProduct.objects.get(pk=product_id)
    temp_product_picture_1 = temp_product.picture_1.url if temp_product.picture_1 else None
    if temp_product_picture_1 is not None:
        picture_path = parent_file_dir + '/media' + temp_product.picture_1.url
        img_thumbnail = start_generating_thumbnail(picture_path)
        temp_product.save_image('picture_1_thumbnail', img_thumbnail)
        # temp_product.picture_1_thumbnail = rename_product_pictures(temp_product.picture_1_thumbnail)
        # temp_product.save()

    temp_product_picture_2 = temp_product.picture_2.path if temp_product.picture_2 else None
    if temp_product_picture_2 is not None:
        picture_path = parent_file_dir + '/media' + temp_product.picture_2.url
        img_thumbnail = start_generating_thumbnail(picture_path)
        temp_product.save_image('picture_2_thumbnail', img_thumbnail)
        # temp_product.picture_2_thumbnail = rename_product_pictures(temp_product.picture_2_thumbnail)
        # temp_product.save()

    temp_product_picture_3 = temp_product.picture_3.path if temp_product.picture_3 else None
    if temp_product_picture_3 is not None:
        picture_path = parent_file_dir + '/media' + temp_product.picture_3.url
        img_thumbnail = start_generating_thumbnail(picture_path)
        temp_product.save_image('picture_3_thumbnail', img_thumbnail)
        # temp_product.picture_3_thumbnail = rename_product_pictures(temp_product.picture_3_thumbnail)
        # temp_product.save()

    temp_product_picture_4 = temp_product.picture_4.path if temp_product.picture_4 else None
    if temp_product_picture_4 is not None:
        picture_path = parent_file_dir + '/media' + temp_product.picture_4.url
        img_thumbnail = start_generating_thumbnail(picture_path)
        temp_product.save_image('picture_4_thumbnail', img_thumbnail)
        # temp_product.picture_4_thumbnail = rename_product_pictures(temp_product.picture_4_thumbnail)
        # temp_product.save()
