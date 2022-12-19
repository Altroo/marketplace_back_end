from typing import Union
from django.db.models import QuerySet
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from order.models import Order
from order.base.serializers import BaseOrdersListSerializerV2
from order.base.filters import OrderStatusFilterSet

# class OrdersView(APIView, PageNumberPagination):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def get(self, request, *args, **kwargs):
#         user = request.user
#         orders: Union[QuerySet, Order] = Order.objects.filter(seller__user=user) \
#             .prefetch_related('order_details_order').order_by('-order_date')
#         page = self.paginate_queryset(request=request, queryset=orders)
#         if page is not None:
#             serializer = BaseOrdersListSerializerV2(instance=page, many=True)
#             return self.get_paginated_response(serializer.data)


class OrdersView(ListAPIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = OrderStatusFilterSet
    serializer_class = BaseOrdersListSerializerV2
    http_method_names = ('get',)

    def get_queryset(self) -> Union[QuerySet, Order]:
        user = self.request.user
        return Order.objects.filter(seller__user=user) \
            .prefetch_related('order_details_order')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filter_queryset: QuerySet = self.filter_queryset(queryset)
        page = self.paginate_queryset(filter_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class GetOrderDetailsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        order_pk = kwargs.get('order_pk')
        try:
            order = Order.objects.get(pk=order_pk, seller__user=user)
            serializer = BaseOrdersListSerializerV2(instance=order)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            errors = {"errors": ["Order Doesn't exist!"]}
            raise ValidationError(errors)


class CancelAllView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        order_pk = request.data.get('order_pk')
        try:
            order = Order.objects.get(pk=order_pk, seller__user=user)
            order.order_status = 'CA'
            order.save(update_fields=['order_status'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            errors = {"error": ["Order doesn't exist!"]}
            raise ValidationError(errors)


class AcceptOrdersView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        order_pk = request.data.get('order_pk')
        try:
            order = Order.objects.get(pk=order_pk, seller__user=user)
            order_details = order.order_details_order.all()
            # Reduce quantity of products.
            # Case offer was deleted & no longer available
            for order_detail in order_details:
                if order_detail.offer_type == 'V':
                    try:
                        product_quantity = order_detail.offer.offer_products.product_quantity
                        # Check for selected positive quantity
                        if isinstance(product_quantity, int) and product_quantity > 0:
                            product_quantity -= order_detail.picked_quantity
                            if product_quantity >= 0:
                                order_detail.offer.offer_products.product_quantity = product_quantity
                            else:
                                order_detail.offer.offer_products.product_quantity = 0
                            order_detail.offer.offer_products.save(update_fields=['product_quantity'])
                    except AttributeError:
                        pass
            order.order_status = 'CM'
            order.save(update_fields=['order_status'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            errors = {"error": ["Order doesn't exist!"]}
            raise ValidationError(errors)
