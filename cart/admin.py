from django.contrib import admin
from django.contrib.admin import ModelAdmin
from cart.models import Cart


class CartAdmin(ModelAdmin):
    list_display = ('pk', 'unique_id', 'picked_color', 'picked_size', 'picked_quantity',
                    'picked_date', 'picked_hour',
                    'created_date', 'updated_date')
    search_fields = ('pk', 'unique_id', 'offer__title', 'picked_size',
                     'picked_date', 'picked_hour')
    ordering = ('-updated_date', '-created_date')


admin.site.register(Cart, CartAdmin)
