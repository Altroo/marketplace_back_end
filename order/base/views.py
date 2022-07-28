from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from order.base.pagination import GetMyOrderDetailsPagination
from shop.models import AuthShop
from order.models import Order, OrderDetails
from order.base.serializers import BaseOrdersListSerializer


class GetMySellingOrdersListView(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user_pk = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user_pk)
            order = Order.objects.filter(seller=auth_shop)
            page = self.paginate_queryset(request=request, queryset=order)
            if page is not None:
                serializer = BaseOrdersListSerializer(instance=page, many=True, context={'order_type': 'sell'})
                return self.get_paginated_response(serializer.data)
        except AuthShop.DoesNotExist:
            data = {'errors': ["User doesn't own a store yet."]}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetMyBuyingsOrdersListView(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user_pk = request.user
        order = Order.objects.filter(buyer=user_pk)
        page = self.paginate_queryset(request=request, queryset=order)
        if page is not None:
            serializer = BaseOrdersListSerializer(instance=page, many=True, context={'order_type': 'buy'})
            return self.get_paginated_response(serializer.data)


# class GetMyOrderDetailsView(APIView):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     @staticmethod
#     def get(request, *args, **kwargs):
#         user = request.user
#         order_pk = kwargs.get('order_pk')
#         order_type = kwargs.get('order_type')
#         try:
#             if order_type == 'buy':
#                 order = Order.objects.get(pk=order_pk, buyer=user)
#             else:
#                 order = Order.objects.get(pk=order_pk, seller__user=user)
#             order_details = OrderDetails.objects.filter(order=order)
#             offer_details_serializer = BaseOrderDetailsListSerializer(order_details,
#                                                                       context={'order_type': order_type},
#                                                                       many=True)
#             # Mark Order as viewed True (buyer or seller)
#             # TODO Add ws event order viewed
#             if order_type == 'buy':
#                 order.viewed_buyer = True
#                 order.save()
#             else:
#                 order.viewed_seller = True
#                 order.save()
#             return Response(offer_details_serializer.data, status=status.HTTP_200_OK)
#         except Order.DoesNotExist:
#             data = {'errors': ['Order not found.']}
#             return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetMyOrderDetailsViewV2(APIView, GetMyOrderDetailsPagination):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        order_pk = kwargs.get('order_pk')
        order_type = kwargs.get('order_type')
        if order_type == 'buy':
            order = Order.objects.get(pk=order_pk, buyer=user)
        else:
            order = Order.objects.get(pk=order_pk, seller__user=user)
        order_details = OrderDetails.objects.filter(order=order)
        total_price = 0
        for order_detail in order_details:
            total_price += order_detail.total_self_price
        total_price += order.highest_delivery_price
        page = self.paginate_queryset(request=request, queryset=order_details)
        if page is not None:
            return self.get_paginated_response_custom(order, order_details, total_price, order_type)


class CancelSellingOfferView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        pass


class CancelBuyingOfferView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        pass

