from typing import Union
from os import path
from decouple import config
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.db.models import QuerySet
from django.utils.html import format_html
from seo_pages.models import DefaultSeoPage, HomePage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

parent_file_dir = path.abspath(path.join(path.dirname(__file__), ".."))
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/indexing"]


def get_or_create_credentials():
    creds = None
    if path.exists(parent_file_dir + '/Qaryb_API/google_api/indexing_token.json'):
        creds = Credentials.from_authorized_user_file(
            parent_file_dir + '/Qaryb_API/google_api/indexing_token.json',
            GOOGLE_SCOPES
        )
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                parent_file_dir + '/Qaryb_API/google_api/secret.json',
                GOOGLE_SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(parent_file_dir + '/Qaryb_API/google_api/indexing_token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def insert_event(request_id, response, exception):
    if exception is not None:
        messages.error(request_id, exception)
    else:
        messages.info(request_id, response)


@admin.action(description='Indéxé les pages selectionnez.')
def call_google_index(modeladmin, request, queryset: Union[QuerySet, DefaultSeoPage]):
    urls = [f"https://qaryb.com/collections/{i.page_url}/" for i in queryset]
    urls_to_index = {}
    for url in urls:
        urls_to_index[url] = 'URL_UPDATED'

    credentials = get_or_create_credentials()
    service = build('indexing', 'v3', credentials=credentials)
    batch = service.new_batch_http_request(callback=insert_event)
    for url, api_type in urls_to_index.items():
        batch.add(
            service.urlNotifications().publish(
                body={"url": url, "type": api_type}
            )
        )
    batch.execute()


class DefaultSeoPagesAdmin(ModelAdmin):
    filter_horizontal = ('articles',)
    # show_default_seo_articles
    list_display = ('pk', 'get_page_url', 'title', 'indexed')
    search_fields = ('pk', 'page_url', 'title', 'tags', 'h_one', 'h_two', 'paragraphe',
                     'page_meta_description', 'articles__offer__title',
                     'articles__offer__auth_shop__shop_name')
    list_filter = ('indexed',)
    ordering = ('-pk',)
    actions = [call_google_index]

    @admin.display(description='Page url')
    def get_page_url(self, obj):
        page_url = obj.page_url
        html = f"<a href='{config('FRONT_DOMAIN')}/collections/{page_url}' target='_blank'>{page_url}</a>"
        return format_html(html)


class HomePageAdmin(ModelAdmin):
    list_display = ('coup_de_coeur_bg', 'coup_de_coeur', 'show_new_shops')
    search_fields = ('coup_de_coeur__shop_name', 'coup_de_coeur__qaryb_link',
                     'new_shops__shop_name', 'new_shops__qaryb_link')
    ordering = ('-pk',)

    @admin.display(description='New Shops')
    def show_new_shops(self, obj):
        return ", ".join([i.shop_name for i in obj.new_shops.all()])

    def has_add_permission(self, request):
        return not HomePage.objects.exists()


admin.site.register(DefaultSeoPage, DefaultSeoPagesAdmin)
admin.site.register(HomePage, HomePageAdmin)
