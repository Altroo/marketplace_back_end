from django.contrib import admin
from auth_shop.base.models import AuthShopDays, AuthShop
from django.contrib.admin import ModelAdmin


class CustomAuthShopAdmin(ModelAdmin):
    list_display = ('pk', 'shop_name', 'user')
    search_fields = ('pk', 'shop_name', 'user')
    ordering = ('-pk',)


class CustomDaysAdmin(ModelAdmin):
    list_display = ('pk', 'code_day', 'name_day',)
    search_fields = ('pk', 'code_day', 'name_day',)
    ordering = ('pk',)


admin.site.register(AuthShop, CustomAuthShopAdmin)
admin.site.register(AuthShopDays, CustomDaysAdmin)
