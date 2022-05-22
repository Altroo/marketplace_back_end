from django.contrib import admin
from temp_shop.base.models import TempShop
from django.contrib.admin import ModelAdmin


class CustomTempShopAdmin(ModelAdmin):
    list_display = ('pk', 'shop_name', 'unique_id')
    search_fields = ('pk', 'shop_name', 'unique_id')
    ordering = ('-pk',)


admin.site.register(TempShop, CustomTempShopAdmin)
