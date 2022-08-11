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
            data = {"errors": ["User doesn't own a store yet."]}
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


class GetMyOrderDetailsView(APIView, GetMyOrderDetailsPagination):
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


class CancelOneOrderView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        order_details_pk = request.data.get('order_details_pk')
        try:
            order_detail = OrderDetails.objects.get(pk=order_details_pk)
            # Canceled by the buyer
            if user == order_detail.order.buyer:
                # Cancel only if order still not confirmed
                if order_detail.order_status == 'TC':
                    order_detail.order_status = 'CB'
                    order_detail.save()
            # Canceled by the seller
            # TODO check when it's allowed for seller to cancel
            elif user == order_detail.order.seller.user:
                order_detail.seller_canceled_reason = request.data.get('seller_canceled_reason')
                order_detail.seller_cancel_body = request.data.get('seller_cancel_body', None)
                order_detail.order_status = 'CS'
                order_detail.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except OrderDetails.DoesNotExist:
            data = {
                "errors": "OrderDetail doesn't exist!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class CancelAllView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        order_pk = request.data.get('order_pk')
        try:
            order = Order.objects.get(pk=order_pk)
            # Canceled by the buyer
            if user == order.buyer:
                order_details = OrderDetails.objects.filter(order=order)
                for order_detail in order_details:
                    # Cancel only if order still not confirmed
                    if order_detail.order_status == 'TC':
                        order_detail.order_status = 'CB'
                        order_detail.save()
            # Canceled by the seller
            # TODO check when it's allowed for seller to cancel
            elif user == order.seller.user:
                order_details = OrderDetails.objects.filter(order=order)
                for order_detail in order_details:
                    order_detail.seller_canceled_reason = request.data.get('seller_canceled_reason')
                    order_detail.seller_cancel_body = request.data.get('seller_cancel_body', None)
                    order_detail.order_status = 'CS'
                    order_detail.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            data = {
                "errors": "OrderDetail doesn't exist!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class AcceptOrdersView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        order_pk = request.data.get('order_pk')
        try:
            order = Order.objects.get(pk=order_pk, seller__user=user)
            order_details = OrderDetails.objects.filter(order=order)
            for order_detail in order_details:
                # Accept those with To confirm status only
                if order_detail.order_status == 'TC':
                    # A évaluer
                    if order_detail.offer_type == 'S':
                        # Mark as To evaluate
                        order_detail.order_status = 'TE'
                    # Preparation en cours
                    else:
                        # Mark as on going
                        order_detail.order_status = 'OG'
                        # Reduce quantity of products.
                        # Case offer was deleted & no longer available
                        try:
                            product_quantity = order_detail.offer.offer_products.product_quantity
                            # Check for selected positive quantity
                            if isinstance(product_quantity, int) and product_quantity > 0:
                                product_quantity -= 1
                        except AttributeError:
                            pass
                    order_detail.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            data = {
                "errors": "OrderDetail doesn't exist!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class PatchOrderStatusView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    # TODO fuse patch order status
    # upgrade status each time starting with TE (TO Evaluate)
    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        order_pk = request.data.get('order_pk')
        try:
            order = Order.objects.get(pk=order_pk, seller__user=user)
            order_details = OrderDetails.objects.filter(order=order)
            for order_detail in order_details:
                # Check orders with on going status
                if order_detail.order_status == 'OG':
                    # Prête
                    if order_detail.picked_click_and_collect:
                        # Mark as Ready = click & collect
                        order_detail.order_status = 'RD'
                    # Expidée
                    elif order_detail.picked_delivery:
                        # Mark as Shipped = delivery
                        order_detail.order_status = 'SH'
                    order_detail.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            data = {
                "errors": "OrderDetail doesn't exist!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class AdjustDeliveryPriceView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        order_pk = request.data.get('order_pk')
        new_delivery_price = request.data.get('new_delivery_price')
        try:
            order = Order.objects.get(pk=order_pk, seller__user=user)
            order_details = OrderDetails.objects.filter(order=order)
            # Adjust delivery price to orders that only has To confirm status
            # And those with deliveries
            for order_detail in order_details:
                if order_detail.order_status == 'TC' and order_detail.picked_delivery:
                    order_detail.new_delivery_price_reason = request.data.get('new_delivery_price_reason')
                    order_detail.new_delivery_price_body = request.data.get('new_delivery_price_body', None)
                    order_detail.new_delivery_price = new_delivery_price
                    order_detail.order_status = 'DP'
                    order_detail.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            data = {
                "errors": "OrderDetail doesn't exist!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class AcceptNewAdjustedDeliveryPrice(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        order_pk = request.data.get('order_pk')
        try:
            order = Order.objects.get(pk=order_pk, buyer=user)
            order_details = OrderDetails.objects.filter(order=order)
            for order_detail in order_details:
                # Accept those with Delivery Price adjusted status only
                # And Those with picked delivery
                if order_detail.order_status == 'DP' and order_detail.picked_delivery:
                    order_detail.order_status = 'OG'
                    # Reduce quantity of products.
                    # Case offer was deleted & no longer available
                    try:
                        product_quantity = order_detail.offer.offer_products.product_quantity
                        # Check for selected positive quantity
                        if isinstance(product_quantity, int) and product_quantity > 0:
                            product_quantity -= 1
                    except AttributeError:
                        pass
                    order_detail.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            data = {
                "errors": "OrderDetail doesn't exist!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
