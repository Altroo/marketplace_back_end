from uuid import uuid4
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from pdfkit import from_string
from Qaryb_API.celery_conf import app
from celery.utils.log import get_task_logger
from os import path
from decouple import config
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.mail import get_connection
from shop.models import AuthShop
from Qaryb_API.google_api.google_utils import GoogleUtils

logger = get_task_logger(__name__)


@app.task(bind=True, serializer='pickle')
def base_generate_pdf(self, user_pk, data, subscription):
    base_path = path.join('media/files/')
    pdf_output_path = "{}{}.{}".format(base_path, uuid4(), 'pdf')
    facture_template = 'facture.html'
    html_page = render_to_string(facture_template, {
        'facture_numero': data['facture_numero'],
        'reference_number': data['reference_number'],
        'created_date': data['created_date'],
        'first_name': data['first_name'],
        'last_name': data['last_name'],
        'company': data['company'],
        'ice': data['ice'],
        'adresse': data['adresse'],
        'code_postal': data['code_postal'],
        'city': data['city'],
        'country': data['country'],
        'nbr_article': data['nbr_article'],
        'prix_ht': data['prix_ht'],
        'tva': data['tva'],
        'prix_ttc': data['prix_ttc'],
    })
    from_string(html_page, pdf_output_path)
    subscription.facture = pdf_output_path
    subscription.save(update_fields=['facture'])
    event = {
        "type": "recieve_group_message",
        "message": {
            "type": "FACTURE_PDF",
            "path": subscription.get_absolute_facture_path,
        }
    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)("%s" % user_pk, event)


@app.task(bind=True, serializer='json')
def base_inform_new_shop_subscription(self, shop_pk: int, available_slots: int):
    shop = AuthShop.objects.get(pk=shop_pk)
    host = 'smtp.gmail.com'
    port = 587
    username = 'no-reply@qaryb.com'
    password = '24YAqua09'
    use_tls = True
    mail_subject = f'Nouvelle boutique : {shop.shop_name}'
    mail_template = 'inform_new_subscription.html'
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


@app.task(bind=True, serializer='pickle')
def append_google_sheet_row(self, data, ligne_number, type_):
    google = GoogleUtils()
    google.insert_sheet(data, ligne_number, type_)
