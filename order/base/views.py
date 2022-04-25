from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from auth_shop.base.models import AuthShop
from order.base.models import Order, OrderDetails
from order.base.serializers import BaseTempOrdersListSerializer, BaseOrderDetailsListSerializer


# class GetMyOrdersListView(APIView, PageNumberPagination):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     # TODO include double list orders for buyers & sellers
#     def get(self, request, *args, **kwargs):
#         user_pk = request.user
#         try:
#             auth_shop = AuthShop.objects.get(user=user_pk)
#             temp_shop = Order.objects.filter(seller=auth_shop)
#             page = self.paginate_queryset(request=request, queryset=temp_shop)
#             if page is not None:
#                 serializer = BaseTempOrdersListSerializer(instance=page, many=True)
#                 return self.get_paginated_response(serializer.data)
#         except AuthShop.DoesNotExist:
#             data = {'errors': ['Auth shop not found.']}
#             return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetMySellingOrdersListView(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user_pk = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user_pk)
            temp_shop = Order.objects.filter(seller=auth_shop)
            page = self.paginate_queryset(request=request, queryset=temp_shop)
            if page is not None:
                # TODO pass sell context
                serializer = BaseTempOrdersListSerializer(instance=page, many=True)
                return self.get_paginated_response(serializer.data)
        except AuthShop.DoesNotExist:
            data = {'errors': ["User doesn't own a store yet."]}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetMyBuyingsOrdersListView(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user_pk = request.user
        temp_shop = Order.objects.filter(buyer=user_pk)
        page = self.paginate_queryset(request=request, queryset=temp_shop)
        if page is not None:
            # TODO pass buy context
            serializer = BaseTempOrdersListSerializer(instance=page, many=True)
            return self.get_paginated_response(serializer.data)


class GetMyOrderDetailsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        order_pk = kwargs.get('order_pk')
        order_type = kwargs.get('order_type')
        try:
            if order_type == 'buy':
                order = Order.objects.get(pk=order_pk, buyer=user)
            else:
                order = Order.objects.get(pk=order_pk, seller__user=user)
            order_details = OrderDetails.objects.filter(order=order)
            offer_details_serializer = BaseOrderDetailsListSerializer(order_details, context={'order_type': order_type},
                                                                      many=True)
            return Response(offer_details_serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            data = {'errors': ['Order not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

