from django.contrib import admin
from temp_product.base.models import TempProduct, TempDelivery, TempSolder
from django.contrib.admin import ModelAdmin


class CustomTempProductAdmin(ModelAdmin):
    list_display = ('pk', 'product_type', 'product_name', 'show_categories')
    search_fields = ('pk', 'product_name')
    ordering = ('-pk',)

    @staticmethod
    def show_categories(obj):
        return "\n".join([i.name_category for i in obj.product_category.all()])


class CustomTempDeliveryAdmin(ModelAdmin):
    list_display = ('pk', 'temp_product', 'show_cities', 'temp_delivery_price', 'temp_delivery_days')
    search_fields = ('pk', 'temp_delivery_price', 'temp_delivery_days')
    ordering = ('-pk',)

    @staticmethod
    def show_cities(obj):
        return "\n".join([i.city_en for i in obj.temp_delivery_city.all()])


class CustomTempSolderAdmin(ModelAdmin):
    list_display = ('pk', 'temp_product', 'temp_solder_type', 'temp_solder_value')
    search_fields = ('pk', 'temp_product', 'temp_solder_type', 'temp_solder_value')
    ordering = ('-pk',)


admin.site.register(TempProduct, CustomTempProductAdmin)
admin.site.register(TempDelivery, CustomTempDeliveryAdmin)
admin.site.register(TempSolder, CustomTempSolderAdmin)
