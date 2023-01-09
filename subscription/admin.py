from decouple import config
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import path
from datetime import timedelta
from string import ascii_uppercase
from random import choice
from django.utils import timezone
from django.utils.html import format_html
from subscription.models import AvailableSubscription, RequestedSubscriptions, \
    PromoCodes, SubscribedUsers, IndexedArticles


class CustomAvailableSubscriptionAdmin(ModelAdmin):
    list_display = ('pk', 'nbr_article', 'prix_ht', 'prix_ttc', 'prix_unitaire_ht',
                    'prix_unitaire_ttc', 'pourcentage')
    search_fields = ('pk', 'nbr_article', 'prix_ht', 'prix_ttc', 'prix_unitaire_ht',
                     'prix_unitaire_ttc', 'pourcentage')
    ordering = ('nbr_article',)


class CustomRequestedSubscriptionAdmin(ModelAdmin):
    list_display = ('pk', 'auth_shop', 'subscription',
                    'first_name',
                    'last_name', 'reference_number', 'facture_number',
                    'status', 'created_date', 'updated_date')
    search_fields = ('pk', 'auth_shop', 'subscription',
                     'reference_number', 'facture_number', 'company', 'ice', 'first_name',
                     'last_name', 'adresse', 'city', 'code_postal',
                     'country__name_fr', 'promo_code__promo_code',
                     'status', 'created_date', 'updated_date')
    list_filter = ('status', 'subscription', 'payment_type')
    date_hierarchy = 'created_date'
    ordering = ('-pk',)


class CustomPromoCodesAdmin(ModelAdmin):
    change_list_template = "generate_promo_code.html"

    list_display = ('pk', 'promo_code', 'type_promo_code', 'usage_unique', 'value', 'promo_code_status',
                    'expiration_date')
    search_fields = ('pk', 'promo_code', 'type_promo_code', 'usage_unique', 'value', 'promo_code_status',
                     'expiration_date')
    list_filter = ('type_promo_code', 'usage_unique', 'promo_code_status')
    ordering = ('-pk',)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('generate_promo_code/', self.generate_promo_code),
        ]
        return my_urls + urls

    def generate_promo_code(self, request):
        promo_code = ''.join(
            choice(ascii_uppercase) for _ in range(6)
        )
        expiration_date = timezone.now() + timedelta(weeks=1)
        try:
            self.model.objects.create(
                promo_code=promo_code,
                type_promo_code='S',
                usage_unique=True,
                value=4,
                expiration_date=expiration_date,
            )
            self.message_user(request, "Promo code Generated")
        except IntegrityError:
            self.message_user(request, "Promo code Already exists, click again!", level='ERROR')
        return HttpResponseRedirect("../")


class CustomSubscribedUsersAdmin(ModelAdmin):
    list_display = ('pk', 'original_request', 'available_slots',
                    'total_paid', 'facture', 'expiration_date')
    search_fields = ('pk', 'original_request__auth_shop__shop_name', 'available_slots',
                     'facture', 'expiration_date')
    ordering = ('-pk',)


class CustomIndexedArticlesAdmin(ModelAdmin):
    list_display = ('pk', 'get_article_url', 'get_shop_url', 'show_seo_pages',
                    'created_date', 'updated_date', 'status')
    search_fields = ('pk', 'subscription__original_request__auth_shop__shop_name',
                     'offer__title', 'subscription__original_request__auth_shop__qaryb_link')
    list_editable = ('status',)
    list_filter = ('status', 'created_date', 'updated_date',
                   'subscription__expiration_date', 'default_seo_page_indexed_articles',
                   'subscription__original_request__auth_shop__qaryb_link')
    date_hierarchy = 'updated_date'
    exclude = ('email_informed',)

    @admin.display(description='Seo pages')
    def show_seo_pages(self, obj):
        return "\n".join([i.page_url for i in obj.default_seo_page_indexed_articles.all()])

    @admin.display(description='Article url')
    def get_article_url(self, obj):
        qaryb_link = obj.offer.auth_shop.qaryb_link
        offer_pk = obj.offer.pk
        html = f"<a href='{config('FRONT_DOMAIN')}/shop/{qaryb_link}/article/{offer_pk}' " \
               f"target='_blank'>{obj.offer.title}</a>"
        return format_html(html)

    @admin.display(description='Shop url')
    def get_shop_url(self, obj):
        qaryb_link = obj.offer.auth_shop.qaryb_link
        html = f"<a href='{config('FRONT_DOMAIN')}/shop/{qaryb_link}' target='_blank'>{qaryb_link}</a>"
        return format_html(html)

    @staticmethod
    def expiration_date(obj):
        return obj.subscription.expiration_date

    def get_readonly_fields(self, request, obj=None):
        # fields = super(CustomIndexedArticlesAdmin, self).get_fields(request, obj)
        try:
            groups_list = list(request.user.groups.values_list('name', flat=True))
            if 'Referencement' in groups_list:
                return 'subscription', 'offer', 'created_date', 'updated_date'
            else:
                return 'subscription', 'offer', 'email_informed', 'status', 'created_date', 'updated_date'
        except IndexError:
            pass
        return ()

    # def get_fields(self, request, obj=None):
    #     fields = super(CustomIndexedArticlesAdmin, self).get_fields(request, obj)
    #     try:
    #         groups_list = list(request.user.groups.values_list('name', flat=True))
    #         if 'Referencement' in groups_list:
    #             fields = ('titre_style',)
    #         else:
    #             fields = ['titre_style', 'page_title', 'lien_style',
    #                       'meta_description_style',
    #                       'h1_style', 'h2_style',
    #                       'paragraphe_style', 'referencer_style']
    #     except IndexError:
    #         pass
    #     return fields


admin.site.register(AvailableSubscription, CustomAvailableSubscriptionAdmin)
admin.site.register(RequestedSubscriptions, CustomRequestedSubscriptionAdmin)
admin.site.register(PromoCodes, CustomPromoCodesAdmin)
admin.site.register(SubscribedUsers, CustomSubscribedUsersAdmin)
admin.site.register(IndexedArticles, CustomIndexedArticlesAdmin)
