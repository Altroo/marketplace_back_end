from django.contrib import admin
from temp_shop.base.models import TempShop
from temp_offer.base.models import TempDelivery
from django.contrib.admin import ModelAdmin


class CustomTempShopAdmin(ModelAdmin):
    list_display = ('pk', 'shop_name', 'unique_id')
    search_fields = ('pk', 'shop_name', 'unique_id')
    ordering = ('-pk',)


class CustomTempDeliveryAdmin(ModelAdmin):
    list_display = ('pk', 'temp_offer',
                    'temp_delivery_city_1', 'temp_delivery_price_1', 'temp_delivery_days_1',
                    'temp_delivery_city_2', 'temp_delivery_price_2', 'temp_delivery_days_2',
                    'temp_delivery_city_3', 'temp_delivery_price_3', 'temp_delivery_days_3',
                    )
    search_fields = ('pk',
                     'temp_delivery_city_1', 'temp_delivery_price_1', 'temp_delivery_days_1',
                     'temp_delivery_city_2', 'temp_delivery_price_2', 'temp_delivery_days_2',
                     'temp_delivery_city_3', 'temp_delivery_price_3', 'temp_delivery_days_3',
                     )
    ordering = ('-pk',)


admin.site.register(TempShop, CustomTempShopAdmin)
admin.site.register(TempDelivery, CustomTempDeliveryAdmin)
