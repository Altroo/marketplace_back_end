from django_filters import BaseInFilter
from django_filters.rest_framework import FilterSet, CharFilter, DateFilter
from order.models import Order


class OrderStatusFilterSet(FilterSet):
    order_status = CharFilter()

    class Meta:
        model = Order
        fields = ('order_status',)


class OrderDateFilterSet(FilterSet):
    order_date = DateFilter()

    class Meta:
        model = Order
        fields = ('order_date',)
