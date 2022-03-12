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


# class CustomDeliveryAdmin(ModelAdmin):
#     list_display = ('pk', 'offer',
#                     'delivery_city_1', 'delivery_price_1', 'delivery_days_1',
#                     'delivery_city_2', 'delivery_price_2', 'delivery_days_2',
#                     'delivery_city_3', 'delivery_price_3', 'delivery_days_3',
#                     )
#     search_fields = ('pk',
#                      'delivery_city_1', 'delivery_price_1', 'delivery_days_1',
#                      'delivery_city_2', 'delivery_price_2', 'delivery_days_2',
#                      'delivery_city_3', 'delivery_price_3', 'delivery_days_3',
#                      )
#     ordering = ('-pk',)


admin.site.register(AuthShop, CustomAuthShopAdmin)
admin.site.register(AuthShopDays, CustomDaysAdmin)
