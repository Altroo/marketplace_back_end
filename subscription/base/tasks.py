from uuid import uuid4
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.template.loader import render_to_string
from pdfkit import from_string
from Qaryb_API.celery_conf import app
from celery.utils.log import get_task_logger
from os import path

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
