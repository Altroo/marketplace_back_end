from django.contrib import admin
from .models import Categories, Colors, Sizes, ForWhom, Days
from django.contrib.admin import ModelAdmin


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


class CustomDaysAdmin(ModelAdmin):
    list_display = ('pk', 'code_day', 'name_day',)
    search_fields = ('pk', 'code_day', 'name_day',)
    ordering = ('pk',)


# admin.site.register(AuthShop, CustomAuthShopAdmin)
admin.site.register(Categories, CustomCategoriesAdmin)
admin.site.register(Colors, CustomColorsAdmin)
admin.site.register(Sizes, CustomSizesAdmin)
admin.site.register(ForWhom, CustomForWhomAdmin)
admin.site.register(Days, CustomDaysAdmin)
