from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import path
from datetime import timedelta
from string import ascii_uppercase
from random import choice
from django.utils import timezone

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
    list_display = ('pk', 'subscription',
                    'expiration_date', 'offer', 'offer_title',
                    'created_date', 'updated_date', 'status')
    search_fields = ('pk', 'subscription__original_request__auth_shop__shop_name',
                     'offer__title',)
    list_filter = ('status', 'created_date', 'updated_date')
    date_hierarchy = 'updated_date'

    @staticmethod
    def available_slots(obj):
        return obj.subscription.available_slots

    @staticmethod
    def expiration_date(obj):
        return obj.subscription.expiration_date

    @staticmethod
    def offer_title(obj):
        return obj.offer.title


admin.site.register(AvailableSubscription, CustomAvailableSubscriptionAdmin)
admin.site.register(RequestedSubscriptions, CustomRequestedSubscriptionAdmin)
admin.site.register(PromoCodes, CustomPromoCodesAdmin)
admin.site.register(SubscribedUsers, CustomSubscribedUsersAdmin)
admin.site.register(IndexedArticles, CustomIndexedArticlesAdmin)
