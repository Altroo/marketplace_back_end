from offer.base.models import Categories, Colors, Sizes, ForWhom, \
    Offers, Solder, Products, Services, ServiceDays
from django.contrib import admin
from django.contrib.admin import ModelAdmin


class CustomOfferAdmin(ModelAdmin):
    list_display = ('pk', 'offer_type', 'title', 'show_categories')
    search_fields = ('pk', 'title')
    ordering = ('-pk',)

    @staticmethod
    def show_categories(obj):
        return "\n".join([i.name_category for i in obj.offer_categories.all()])


class CustomSolderAdmin(ModelAdmin):
    list_display = ('pk', 'offer', 'solder_type', 'solder_value')
    search_fields = ('pk', 'offer', 'solder_type', 'solder_value')
    ordering = ('-pk',)


class CustomProductAdmin(ModelAdmin):
    list_display = ('pk', 'offer', 'show_colors', 'show_sizes', 'product_quantity',
                    'product_price_by', 'product_longitude', 'product_latitude', 'product_address')
    search_fields = ('pk', 'offer', 'product_address', 'product_quantity')
    list_filter = ('product_price_by', )
    ordering = ('-pk',)

    @staticmethod
    def show_colors(obj):
        return "\n".join([i.name_color for i in obj.product_colors.all()])

    @staticmethod
    def show_sizes(obj):
        return "\n".join([i.name_size for i in obj.product_sizes.all()])


class CustomServiceAdmin(ModelAdmin):
    list_display = ('pk', 'offer', 'show_availability_days', 'service_morning_hour_from',
                    'service_morning_hour_to', 'service_afternoon_hour_from', 'service_afternoon_hour_to',
                    'service_zone_by', 'service_price_by', 'service_longitude', 'service_latitude',
                    'service_address', 'service_km_radius')
    search_fields = ('pk', 'offer', 'service_morning_hour_from', 'service_morning_hour_to',
                     'service_afternoon_hour_from', 'service_afternoon_hour_to',
                     'service_zone_by', 'service_price_by', 'service_longitude', 'service_latitude',
                     'service_address', 'service_km_radius')
    list_filter = ('service_zone_by', 'service_price_by', )
    ordering = ('-pk',)

    @staticmethod
    def show_availability_days(obj):
        return "\n".join([i.name_day for i in obj.service_availability_days.all()])


class CustomCategoriesAdmin(ModelAdmin):
    list_display = ('pk', 'code_category', 'name_category',)
    search_fields = ('pk', 'code_category', 'name_category',)
    ordering = ('pk',)


class CustomColorsAdmin(ModelAdmin):
    list_display = ('pk', 'code_color', 'name_color',)
    search_fields = ('pk', 'code_color', 'name_color',)
    ordering = ('pk',)


class CustomSizesAdmin(ModelAdmin):
    list_display = ('pk', 'code_size', 'name_size',)
    search_fields = ('pk', 'code_size', 'name_size',)
    ordering = ('pk',)


class CustomForWhomAdmin(ModelAdmin):
    list_display = ('pk', 'code_for_whom', 'name_for_whom',)
    search_fields = ('pk', 'code_for_whom', 'name_for_whom',)
    ordering = ('pk',)


class CustomServiceDaysAdmin(ModelAdmin):
    list_display = ('pk', 'code_day', 'name_day',)
    search_fields = ('pk', 'code_day', 'name_day',)
    ordering = ('pk',)


admin.site.register(Categories, CustomCategoriesAdmin)
admin.site.register(Colors, CustomColorsAdmin)
admin.site.register(Sizes, CustomSizesAdmin)
admin.site.register(ForWhom, CustomForWhomAdmin)
admin.site.register(ServiceDays, CustomServiceDaysAdmin)
admin.site.register(Offers, CustomOfferAdmin)
admin.site.register(Solder, CustomSolderAdmin)
admin.site.register(Products, CustomProductAdmin)
admin.site.register(Services, CustomServiceAdmin)
