from django.contrib import admin
from django.contrib.admin import ModelAdmin
from order.base.models import Order, OrderDetails


class OrderAdmin(ModelAdmin):
    list_display = ('pk', 'buyer', 'seller',
                    'order_number', 'order_date', 'order_status')
    search_fields = ('pk', 'buyer__email', 'seller__shop_name', 'order_number')
    list_filter = ('order_status',)
    ordering = ('-order_date',)
    # date_hierarchy = ('-order_date',)


class OrderDetailsAdmin(ModelAdmin):
    list_display = ('pk', 'order', 'offer', 'total_self_price')
    search_fields = ('pk', 'order__buyer__email', 'order__seller__shop_name', 'order__order_number')
    list_filter = ('order__order_status',)
    ordering = ('-order__order_date',)
    # date_hierarchy = ('-order__order_date',)


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderDetails, OrderDetailsAdmin)
