from io import BytesIO
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.mail import get_connection
from subscription.models import IndexedArticles
from Qaryb_API.celery_conf import app
from celery.utils.log import get_task_logger
from shop.models import AuthShop, ModeVacance
from offers.base.tasks import generate_images_v2
from os import path
from account.models import CustomUser
from collections import defaultdict

logger = get_task_logger(__name__)
parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))


@app.task(bind=True, serializer='pickle')
def base_resize_avatar_thumbnail(self, object_pk: int, which: str, avatar: BytesIO | None):
    if which == 'AuthShop':
        object_ = AuthShop.objects.get(pk=object_pk)
    else:
        object_ = CustomUser.objects.get(pk=object_pk)
    if isinstance(avatar, BytesIO):
        generate_images_v2(object_, avatar, 'avatar')
        if which == 'AuthShop':
            event = {
                "type": "recieve_group_message",
                "message": {
                    "type": "SHOP_AVATAR",
                    "pk": object_.user.pk,
                    "avatar": object_.get_absolute_avatar_img,
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
                    "avatar": object_.get_absolute_avatar_img,
                }
            }
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)("%s" % object_.pk, event)
        else:
            # No event for TempShop user is not known yet.
            pass


@app.task(bind=True, serializer='json')
def base_inform_new_shop(self, shop_pk: int, available_slots: int):
    shop = AuthShop.objects.get(pk=shop_pk)
    host = 'smtp.gmail.com'
    port = 587
    username = 'no-reply@qaryb.com'
    password = '24YAqua09'
    use_tls = True
    mail_subject = f'Nouvelle boutique : {shop.shop_name}'
    mail_template = 'inform_new_store.html'
    message = render_to_string(mail_template, {
        'shop_name': shop.shop_name,
        'available_slots': available_slots,
        'shop_link': f"{config('FRONT_DOMAIN')}/shop/{shop.qaryb_link}"
    })
    with get_connection(host=host,
                        port=port,
                        username=username,
                        password=password,
                        use_tls=use_tls) as connection:
        email = EmailMessage(
            mail_subject,
            message,
            to=('yousra@qaryb.com', 'n.hilale@qaryb.com'),
            connection=connection,
            from_email='no-reply@qaryb.com',
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)


# To avoid circular import
@app.task(bind=True, serializer='json')
def base_inform_indexed_articles(self):
    indexed_articles = IndexedArticles.objects.filter(email_informed=False).all()

    data = defaultdict(list)

    for article in indexed_articles:
        data[article.offer.auth_shop.qaryb_link].append(article.offer.pk)

    if indexed_articles.count() > 0:
        host = 'smtp.gmail.com'
        port = 587
        username = 'no-reply@qaryb.com'
        password = '24YAqua09'
        use_tls = True
        mail_subject = f'Nouveau articles référencés'
        mail_template = 'inform_new_indexed_articles.html'
        message = render_to_string(mail_template, {
            'articles': data,
            'front_domain': f"{config('FRONT_DOMAIN')}",
        })
        with get_connection(host=host,
                            port=port,
                            username=username,
                            password=password,
                            use_tls=use_tls) as connection:
            email = EmailMessage(
                mail_subject,
                message,
                to=('yousra@qaryb.com', 'n.hilale@qaryb.com'),
                connection=connection,
                from_email='no-reply@qaryb.com',
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)
            indexed_articles.update(email_informed=True)


@app.task(bind=True, serializer='json')
def base_delete_mode_vacance_obj(self, auth_shop_pk):
    try:
        ModeVacance.objects.get(auth_shop=auth_shop_pk).delete()
    except ModeVacance.DoesNotExist:
        pass

# @app.task(bind=True)
# def base_start_deleting_expired_shops(self, shop_pk):
#     shop = TempShop.objects.get(pk=shop_pk)
#     if shop.unique_id is not None:
#         # Delete avatar image
#         try:
#             avatar_img = shop.avatar.path
#             remove(avatar_img)
#         except (FileNotFoundError, ValueError, AttributeError):
#             pass
#         # Delete avatar thumbnail
#         try:
#             avatar_thumbnail_img = shop.avatar_thumbnail.path
#             remove(avatar_thumbnail_img)
#         except (FileNotFoundError, ValueError, AttributeError):
#             pass
#         # Delete temp product images
#         products = TempOffers.objects.filter(auth_shop=shop.pk)
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
#         shop.delete()
