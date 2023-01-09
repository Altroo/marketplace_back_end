from django.contrib import admin
from django.urls import reverse

from shop.models import AuthShopDays, AuthShop, \
    PhoneCodes, AskForCreatorLabel, ModeVacance
from django.contrib.admin import ModelAdmin, SimpleListFilter
from decouple import config
from django.utils.html import format_html
from django.utils import timezone
from subscription.models import SubscribedUsers, IndexedArticles
from django.db.models import Q
from offers.models import Offers


class AbonnementStatusFilter(SimpleListFilter):
    title = "Abonnement"  # a label for our filter
    parameter_name = "abo"  # you can put anything here

    def lookups(self, request, model_admin):
        # This is where you create filter options; we have two:
        return [
            ("A", "Payant"),
            ("R", "Gratuit"),
            ("P", "En attente"),
            ("E", "Expirer"),
        ]

    def queryset(self, request, queryset):
        # This is where you process parameters selected by use via filter options:
        if self.value() == "A":
            return queryset.distinct().filter(auth_shop_requested_subscription__status='A')
        elif self.value() == "R":
            return queryset.distinct().filter(auth_shop_requested_subscription__status='R')
        elif self.value() == "P":
            return queryset.distinct().filter(auth_shop_requested_subscription__status='P')
        elif self.value() == "E":
            return queryset.distinct().filter(
                auth_shop_requested_subscription__original_request_subscribed_users__expiration_date__lt=timezone.now())
        else:
            return queryset.distinct()


class CustomAuthShopAdmin(ModelAdmin):
    list_display = ('pk', 'get_qaryb_link', 'get_nbr_article', 'get_nbr_article_referencer', 'creator')
    search_fields = ('pk', 'shop_name', 'qaryb_link', 'user')
    list_filter = ('created_date', AbonnementStatusFilter)
    date_hierarchy = 'updated_date'
    ordering = ('-pk',)

    @admin.display(description='Lien boutique')
    def get_qaryb_link(self, obj):
        html = f"<a href='{config('FRONT_DOMAIN')}/shop/{obj.qaryb_link}' target='_blank'>{obj.shop_name}</a>"
        return format_html(html)

    @admin.display(description="Nbr d'article")
    def get_nbr_article(self, obj):
        # subscription = SubscribedUsers.objects.get(original_request__auth_shop=obj)
        # nbr_article = subscription.available_slots
        nbr_article = Offers.objects.filter(auth_shop=obj).count()
        html = '<a href="{reverse}?subscription__original_request__auth_shop__qaryb_link={params}">{nbr}</a>'
        return format_html(html.format(reverse=reverse('admin:subscription_indexedarticles_changelist'),
                                       nbr=nbr_article, params=obj.qaryb_link))

    get_nbr_article.allow_tags = True

    @admin.display(description="Nbr d'article référencés")
    def get_nbr_article_referencer(self, obj):
        subscription = SubscribedUsers.objects.get(original_request__auth_shop=obj)
        nbr_article = subscription.available_slots
        article_referencer = IndexedArticles.objects.filter(~Q(status='P'), offer__auth_shop=obj).count()
        html = f'<a href="{reverse("admin:subscription_indexedarticles_changelist")}' \
               f'?subscription__original_request__auth_shop__qaryb_link={obj.qaryb_link}' \
               f'&status__exact=I">{article_referencer}/{nbr_article}</a>'
        return format_html(html)


class CustomDaysAdmin(ModelAdmin):
    list_display = ('pk', 'code_day', 'name_day',)
    search_fields = ('pk', 'code_day', 'name_day',)
    ordering = ('-pk',)

    # Add permission removed
    def has_add_permission(self, *args, **kwargs):
        return False

    # Delete permission removed
    def has_delete_permission(self, *args, **kwargs):
        return False


class CustomPhoneCodesAdmin(ModelAdmin):
    list_display = ('pk', 'phone_code')
    search_fields = ('pk', 'phone_code')
    ordering = ('-pk',)

    # Add permission removed
    def has_add_permission(self, *args, **kwargs):
        return False

    # Delete permission removed
    def has_delete_permission(self, *args, **kwargs):
        return False


class CustomAskForCreatorLabelAdmin(ModelAdmin):
    list_display = ('pk', 'auth_shop', 'status', 'asked_counter', 'created_date', 'updated_date')
    list_editable = ('status',)
    search_fields = ('pk', 'auth_shop__shop_name')
    list_filter = ('status',)
    ordering = ('-pk',)
    date_hierarchy = 'created_date'

    def save_model(self, request, obj, form, change):
        auth_shop = AuthShop.objects.get(pk=obj.auth_shop.pk)
        # Confirmed
        if obj.status == 'C':
            auth_shop.creator = True
        # Rejected
        elif obj.status == 'R':
            auth_shop.creator = False
        # Default : Awaiting confirmation
        else:
            auth_shop.creator = False
        auth_shop.save()
        super(CustomAskForCreatorLabelAdmin, self).save_model(request, obj, form, change)

    # # Add permission removed
    # def has_add_permission(self, *args, **kwargs):
    #     return False
    #
    # # Delete permission removed
    # def has_delete_permission(self, *args, **kwargs):
    #     return False


class CustomModeVacanceAdmin(ModelAdmin):
    list_display = ('pk', 'auth_shop', 'date_from', 'date_to')
    search_fields = ('pk', 'auth_shop', 'date_from', 'date_to')
    ordering = ('-pk',)
    #
    # # Add permission removed
    # def has_add_permission(self, *args, **kwargs):
    #     return False
    #
    # # Delete permission removed
    # def has_delete_permission(self, *args, **kwargs):
    #     return False


admin.site.register(AuthShop, CustomAuthShopAdmin)
admin.site.register(AuthShopDays, CustomDaysAdmin)
admin.site.register(PhoneCodes, CustomPhoneCodesAdmin)
admin.site.register(AskForCreatorLabel, CustomAskForCreatorLabelAdmin)
admin.site.register(ModeVacance, CustomModeVacanceAdmin)
