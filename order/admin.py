from django.contrib import admin
from django.contrib.admin import ModelAdmin
from order.models import Order, OrderDetails


class OrderAdmin(ModelAdmin):
    list_display = ('pk', 'buyer', 'seller',
                    'order_number', 'order_date', 'order_status')
    search_fields = ('pk', 'first_name', 'last_name', 'shop_name', 'order_number')
    list_filter = ('order_status',)
    ordering = ('-order_date',)


class OrderDetailsAdmin(ModelAdmin):
    list_display = ('pk', 'order', 'total_self_price')
    search_fields = ('pk', 'order__first_name', 'order__last_name',
                     'order__shop_name', 'order__order_number')
    list_filter = ('order__order_status', 'offer_canceled')
    ordering = ('-order__order_date',)


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderDetails, OrderDetailsAdmin)
