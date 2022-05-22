from django.contrib import admin
from temp_offer.base.models import TempOffers, TempSolder, TempProducts, TempServices, TempDelivery
from django.contrib.admin import ModelAdmin


class CustomTempOfferAdmin(ModelAdmin):
    list_display = ('pk', 'offer_type', 'title', 'show_categories')
    search_fields = ('pk', 'title')
    ordering = ('-pk',)

    @staticmethod
    def show_categories(obj):
        return "\n".join([i.name_category for i in obj.offer_categories.all()])


class CustomTempSolderAdmin(ModelAdmin):
    list_display = ('pk', 'temp_offer', 'temp_solder_type', 'temp_solder_value')
    search_fields = ('pk', 'temp_offer', 'temp_solder_type', 'temp_solder_value')
    ordering = ('-pk',)


class CustomTempProductAdmin(ModelAdmin):
    list_display = ('pk', 'temp_offer', 'show_colors', 'show_sizes', 'product_quantity',
                    'product_price_by', 'product_longitude', 'product_latitude', 'product_address')
    search_fields = ('pk', 'temp_offer', 'product_address', 'product_quantity')
    list_filter = ('product_price_by', )
    ordering = ('-pk',)

    @staticmethod
    def show_colors(obj):
        return "\n".join([i.name_color for i in obj.product_colors.all()])

    @staticmethod
    def show_sizes(obj):
        return "\n".join([i.name_size for i in obj.product_sizes.all()])


class CustomTempServiceAdmin(ModelAdmin):
    list_display = ('pk', 'temp_offer', 'show_availability_days', 'service_morning_hour_from',
                    'service_morning_hour_to', 'service_afternoon_hour_from', 'service_afternoon_hour_to',
                    'service_zone_by', 'service_price_by', 'service_longitude', 'service_latitude',
                    'service_address', 'service_km_radius')
    search_fields = ('pk', 'temp_offer', 'service_morning_hour_from', 'service_morning_hour_to',
                     'service_afternoon_hour_from', 'service_afternoon_hour_to',
                     'service_zone_by', 'service_price_by', 'service_longitude', 'service_latitude',
                     'service_address', 'service_km_radius')
    list_filter = ('service_zone_by', 'service_price_by', )
    ordering = ('-pk',)

    @staticmethod
    def show_availability_days(obj):
        return "\n".join([i.name_day for i in obj.service_availability_days.all()])


class CustomTempDeliveryAdmin(ModelAdmin):
    list_display = ('pk', 'temp_offer', 'show_cities', 'temp_delivery_price', 'temp_delivery_days')
    search_fields = ('pk', 'temp_delivery_price', 'temp_delivery_days')
    ordering = ('-pk',)

    @staticmethod
    def show_cities(obj):
        return "\n".join([i.name_fr for i in obj.temp_delivery_city.all()])


admin.site.register(TempDelivery, CustomTempDeliveryAdmin)
admin.site.register(TempOffers, CustomTempOfferAdmin)
admin.site.register(TempSolder, CustomTempSolderAdmin)
admin.site.register(TempProducts, CustomTempProductAdmin)
admin.site.register(TempServices, CustomTempServiceAdmin)
