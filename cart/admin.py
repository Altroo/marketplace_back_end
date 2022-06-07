from django.contrib import admin
from django.contrib.admin import ModelAdmin
from cart.models import Cart


class CartAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'picked_color', 'picked_size', 'picked_quantity',
                    'created_date', 'updated_date')
    search_fields = ('pk', 'user__email', 'offer__title')
    ordering = ('-created_date', '-updated_date')


admin.site.register(Cart, CartAdmin)
