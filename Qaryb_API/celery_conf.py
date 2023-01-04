from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from django.core.mail import get_connection, EmailMessage
from django.template.loader import render_to_string

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
        'offers.base.tasks',
        'order.base.tasks',
        'shop.base.tasks',
        'chat.base.tasks',
        'subscription.base.tasks',
    )
)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Executes every day at midnight
    sender.add_periodic_task(
        crontab(hour=00, minute=00),
        base_inform_marketing_team_new_offer.s('hello'),
    )


@app.task(bind=True, serializer='json')
def base_inform_marketing_team_new_offer(self, arg):
    # Fixes Apps aren't loaded yet
    from subscription.models import IndexedArticles

    indexed_articles = IndexedArticles.objects.filter(email_informed=False).all()
    host = 'smtp.gmail.com'
    port = 587
    username = 'no-reply@qaryb.com'
    password = '24YAqua09'
    use_tls = True
    mail_subject = f'Nouveau articles référencés'
    mail_template = 'inform_new_indexed_articles.html'
    message = render_to_string(mail_template, {
        'articles': indexed_articles,
    })
    with get_connection(host=host,
                        port=port,
                        username=username,
                        password=password,
                        use_tls=use_tls) as connection:
        email = EmailMessage(
            mail_subject,
            message,
            to=('ichrak@qaryb.com', 'yousra@qaryb.com', 'n.hilale@qaryb.com'),
            connection=connection,
            from_email='no-reply@qaryb.com',
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)
        indexed_articles.update(email_informed=True)


@app.task(bind=True, serializer='json')
def debug_task(self):
    print(f'Request: {self.request!r}')
