from decouple import config
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html

from order.models import Order, OrderDetails


class OrderAdmin(ModelAdmin):
    list_display = ('pk', 'first_name', 'seller',
                    'order_number', 'order_date')
    search_fields = ('pk', 'first_name', 'last_name', 'shop_name', 'order_number')
    list_filter = ('order_status', 'order_date')
    ordering = ('-order_date',)


class OrderDetailsAdmin(ModelAdmin):
    list_display = ('pk', 'get_seller', 'get_seller_shop_link', 'get_offer_title', 'get_offer_price',
                    'get_order_number', 'get_order_status')
    search_fields = ('pk', 'order__first_name', 'order__last_name',
                     'order__shop_name', 'order__order_number')
    list_filter = ('order__order_status', 'order__order_date')
    ordering = ('-order__order_date',)

    @admin.display(description='Order number')
    def get_order_number(self, obj):
        return obj.order.order_number

    @admin.display(description='Seller')
    def get_seller(self, obj):
        return obj.order.seller.shop_name

    @admin.display(description='Shop link')
    def get_seller_shop_link(self, obj):
        qaryb_link = obj.order.seller.qaryb_link
        html = f"<a href='{config('FRONT_DOMAIN')}/shop/{qaryb_link}' target='_blank'>{qaryb_link}</a>"
        return format_html(html)

    @admin.display(description='Offer title')
    def get_offer_title(self, obj):
        return obj.offer.title

    @admin.display(description='Offer price')
    def get_offer_price(self, obj):
        return f'{obj.offer.price} DH'

    @admin.display(description='Order status')
    def get_order_status(self, obj):
        return obj.order.get_order_status_display()


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderDetails, OrderDetailsAdmin)
