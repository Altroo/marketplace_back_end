from typing import Union
from django.db.models import QuerySet
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from order.models import Order
from order.base.serializers import BaseOrdersListSerializer, \
    BaseChiffreAffaireListSerializer
from order.base.filters import OrderStatusFilterSet
from django.db.models import Q


class ShopSellingOrdersView(ListAPIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = OrderStatusFilterSet
    serializer_class = BaseOrdersListSerializer
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


class ShopBuyingOrdersView(ListAPIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = OrderStatusFilterSet
    serializer_class = BaseOrdersListSerializer
    http_method_names = ('get',)

    def get_queryset(self) -> Union[QuerySet, Order]:
        user = self.request.user
        return Order.objects.filter(buyer=user) \
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
        sell_order = Order.objects.filter(seller__user=user, pk=order_pk)
        buy_order = Order.objects.filter(buyer=user, pk=order_pk)
        if sell_order:
            serializer = BaseOrdersListSerializer(instance=sell_order[0], context={'order_for': 'S'})
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        if buy_order:
            serializer = BaseOrdersListSerializer(instance=buy_order[0], context={'order_for': 'B'})
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        if not sell_order or not buy_order:
            errors = {"errors": ["Order Doesn't exist!"]}
            raise ValidationError(errors)

    @staticmethod
    def get_offer_total_price(instance, offer_type):
        offer_price = instance.offer_price
        if offer_type == 'V':
            if instance.picked_quantity:
                return offer_price * instance.picked_quantity
            else:
                return offer_price
        else:
            return offer_price

    # def get(self, request, *args, **kwargs):
    #     user = request.user
    #     order_pk = kwargs.get('order_pk')
    #     results_list = []
    #     try:
    #         order = Order.objects.get(pk=order_pk, seller__user=user)
    #         product_offers = order.order_details_order.all().exclude(offer_type='S')
    #         click_and_collect_offers = product_offers.exclude(picked_delivery=False)
    #         lot_1 = False
    #         lot_2 = False
    #         lot_1_pks_to_exclude = []
    #         if click_and_collect_offers:
    #             details_dict = {}
    #             lot_1_list = []
    #             offres_dict = {}
    #             product_longitude = False
    #             product_latitude = False
    #             product_address = False
    #             for i in click_and_collect_offers:
    #                 lot_1_pks_to_exclude.append(i.pk)
    #                 product_longitude = i.product_longitude
    #                 product_latitude = i.product_latitude
    #                 product_address = i.product_address
    #                 lot_1_dict = {
    #                     "order_details_pk": i.pk,
    #                     "offer_pk": i.offer.pk,
    #                     "offer_type": i.offer_type,
    #                     "offer_picture": i.get_absolute_offer_thumbnail,
    #                     "offer_title": i.offer_title,
    #                     "order_status": order.order_status,
    #                     "offer_total_price": self.get_offer_total_price(i, 'V'),
    #                     "offer_details": {
    #                         "picked_color": i.picked_color,
    #                         "picked_size": i.picked_size,
    #                         "picked_quantity": i.picked_quantity,
    #                     }
    #                 }
    #                 lot_1_list.append(lot_1_dict)
    #             if product_longitude and product_latitude and product_address:
    #                 click_and_collect = {
    #                     "product_longitude": product_longitude,
    #                     "product_latitude": product_latitude,
    #                     "product_address": product_address,
    #                 }
    #                 offres_dict['click_and_collect'] = click_and_collect
    #             else:
    #                 offres_dict['click_and_collect'] = {}
    #             offres_dict["order_details"] = lot_1_list
    #             offres_dict['global_offer_type'] = 'V'
    #             # Lot 1
    #             details_dict["lot"] = offres_dict
    #             lot_1 = True
    #             results_list.append(details_dict)
    #
    #         # Check for Lot 2
    #         # deliveries + click & collect
    #         click_and_collect_deliveries_offers = product_offers.exclude(pk__in=lot_1_pks_to_exclude)
    #         if click_and_collect_deliveries_offers:
    #             details_dict = {}
    #             lot_1_list = []
    #             offres_dict = {}
    #             product_longitude = False
    #             product_latitude = False
    #             product_address = False
    #             list_of_cities = []
    #             list_of_prices = []
    #             list_of_days = []
    #             deliveries_output = []
    #             for i in click_and_collect_deliveries_offers:
    #                 product_longitude = i.product_longitude
    #                 product_latitude = i.product_latitude
    #                 product_address = i.product_address
    #                 lot_1_dict = {
    #                     "order_details_pk": i.pk,
    #                     "offer_pk": i.offer.pk,
    #                     "offer_type": i.offer_type,
    #                     "offer_picture": i.get_absolute_offer_thumbnail,
    #                     "offer_title": i.offer_title,
    #                     "order_status": order.order_status,
    #                     "offer_total_price": self.get_offer_total_price(i, 'V'),
    #                     "offer_details": {
    #                         "picked_color": i.picked_color,
    #                         "picked_size": i.picked_size,
    #                         "picked_quantity": i.picked_quantity,
    #                     }
    #                 }
    #                 lot_1_list.append(lot_1_dict)
    #             if product_longitude and product_latitude and product_address:
    #                 click_and_collect = {
    #                     "product_longitude": product_longitude,
    #                     "product_latitude": product_latitude,
    #                     "product_address": product_address,
    #                 }
    #                 offres_dict['click_and_collect'] = click_and_collect
    #             else:
    #                 offres_dict['click_and_collect'] = {}
    #
    #         # Missing
    #         # Avatar - order_date - articles_count - total_price - note - highest_delivery_price
    #         # serializer = BaseGetOrderDetailsSerializer(instance=order)
    #         # return Response(data=serializer.data, status=status.HTTP_200_OK)
    #     except Order.DoesNotExist:
    #         errors = {"errors": ["Order Doesn't exist!"]}
    #         raise ValidationError(errors)

    # def get(self, request, *args, **kwargs):
    #     user = request.user
    #     order_pk = kwargs.get('order_pk')
    #     results_list = []
    #     try:
    #         order = Order.objects.get(pk=order_pk, seller__user=user)
    #         offers = order.order_details_order.all()
    #         click_and_collect_offers = offers.filter(picked_click_and_collect=True)
    #         lot_1 = False
    #         lot_2 = False
    #         click_and_collect_list = defaultdict(list)
    #         if click_and_collect_offers:
    #             for i in click_and_collect_offers:
    #                 click_and_collect_dict = {
    #                     'product_longitude': i.product_longitude,
    #                     'product_latitude': i.product_latitude,
    #                     'product_address': i.product_address,
    #                 }
    #                 if len(click_and_collect_list) > 0:
    #                     for key, value in click_and_collect_list.items():
    #                         if click_and_collect_dict != value:
    #                             click_and_collect_list[i.pk].append(click_and_collect_dict)
    #                 else:
    #                     click_and_collect_list[i.pk].append(click_and_collect_dict)
    #         print(click_and_collect_list)
    #         # Missing
    #         # Avatar - order_date - articles_count - total_price - note - highest_delivery_price
    #         # serializer = BaseGetOrderDetailsSerializer(instance=order)
    #         # return Response(data=serializer.data, status=status.HTTP_200_OK)
    #     except Order.DoesNotExist:
    #         errors = {"errors": ["Order Doesn't exist!"]}
    #         raise ValidationError(errors)


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
            if order.order_status == 'IP':
                order.order_status = 'CM'
                order.save(update_fields=['order_status'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            errors = {"error": ["Order doesn't exist!"]}
            raise ValidationError(errors)


class GetChiffreAffaireListView(ListAPIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = OrderStatusFilterSet
    serializer_class = BaseChiffreAffaireListSerializer
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


class GetNewOrdersCountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        orders_count = Order.objects.filter(seller__user=user, order_status='CM').count()
        data = {
            'orders_count': orders_count,
        }
        return Response(data=data, status=status.HTTP_200_OK)
