from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Qaryb_API.settings")

app = Celery('Qaryb_API', broker=settings.CELERY_BROKER_URL)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.timezone = settings.TIME_ZONE
app.conf.setdefault('worker_cancel_long_running_tasks_on_connection_loss', True)
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['application/json', 'application/x-python-serialize']
app.autodiscover_tasks(
    packages=(
        'account.base.tasks',
        'shop.base.tasks',
        'offers.base.tasks',
        'chat.base.tasks',
        'order.base.tasks',
        'subscription.base.tasks',
    )
)


@app.task(bind=True, serializer='json')
def debug_task(self):
    print(f'Request: {self.request!r}')
