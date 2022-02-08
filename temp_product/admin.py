from django.contrib import admin
from temp_product.base.models import TempProduct, TempDelivery
from django.contrib.admin import ModelAdmin


class CustomTempProductAdmin(ModelAdmin):
    list_display = ('pk', 'product_type', 'product_name', 'show_categories')
    search_fields = ('pk', 'product_name')
    ordering = ('-pk',)

    @staticmethod
    def show_categories(obj):
        return "\n".join([i.name_category for i in obj.product_category.all()])


class CustomTempDeliveryAdmin(ModelAdmin):
    list_display = ('pk', 'temp_product', 'temp_delivery_city', 'temp_delivery_price')
    search_fields = ('pk', 'temp_delivery_city', 'temp_delivery_price')
    ordering = ('-pk',)


admin.site.register(TempProduct, CustomTempProductAdmin)
admin.site.register(TempDelivery, CustomTempDeliveryAdmin)
