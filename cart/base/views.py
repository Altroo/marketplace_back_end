from uuid import uuid4
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from shop.models import AuthShop
from notifications.models import Notifications
from offers.models import Delivery
from cart.base.serializers import BaseCartOfferSerializer
from cart.models import Cart
from cart.base.pagination import GetMyCartPagination, GetCartOffersDetailsPagination
from cart.base.utils import GetCartPrices
from datetime import datetime
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from order.base.tasks import base_generate_user_thumbnail, base_duplicate_order_offer_image
from order.base.serializers import BaseOrderSerializer, BaseOrderDetailsSerializer
from collections import Counter


class GetCartOffersDetailsView(APIView, GetCartOffersDetailsPagination):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        shop_pk = kwargs.get('shop_pk')
        if request.user.is_anonymous:
            cart_offers = Cart.objects.filter(unique_id=unique_id, offer__auth_shop=shop_pk) \
                .order_by('-created_date', '-updated_date')
        else:
            cart_offers = Cart.objects.filter(user=request.user, offer__auth_shop=shop_pk) \
                .order_by('-created_date', '-updated_date')
        total_price = GetCartPrices().calculate_total_price(cart_offers)
        page = self.paginate_queryset(request=request, queryset=cart_offers)
        if page is not None:
            if request.user.is_anonymous:
                return self.get_paginated_response_unique_id_custom(unique_id, shop_pk, total_price)
            else:
                return self.get_paginated_response_user_custom(request.user, shop_pk, total_price)


class CartQuantityView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def patch(request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        cart_pk = kwargs.get('cart_pk')
        action_type: str = kwargs.get('action_type')
        try:
            if request.user.is_anonymous:
                cart_offer = Cart.objects.get(unique_id=unique_id, pk=cart_pk)
            else:
                cart_offer = Cart.objects.get(user=request.user, pk=cart_pk)
            if action_type == '+':
                cart_offer.picked_quantity += 1
                cart_offer.save()
            else:
                cart_offer.picked_quantity -= 1
                cart_offer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            errors = {"error": ["Cart offer not found."]}
            raise ValidationError(errors)


class CartOffersView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        offer_pk = request.data.get('offer_pk')
        offer_type = request.data.get('offer_type')
        picked_color = request.data.get('picked_color', None)
        picked_size = request.data.get('picked_size', None)
        picked_quantity = request.data.get('picked_quantity')
        picked_date = request.data.get('picked_date', None)
        picked_hour = request.data.get('picked_hour', None)
        try:
            if request.user.is_anonymous:
                Cart.objects.get(unique_id=unique_id, offer_id=offer_pk)
            else:
                Cart.objects.get(user=request.user, offer_id=offer_pk)
            errors = {"error": ["Already in cart!"]}
            raise ValidationError(errors)
        except Cart.DoesNotExist:
            # Check to not multiply by 0
            if offer_type == 'V':
                if int(picked_quantity) <= 0 or picked_quantity is None:
                    picked_quantity = 1
            else:
                picked_quantity = None
            serializer = BaseCartOfferSerializer(data={
                "unique_id": unique_id if request.user.is_anonymous else None,
                "user": request.user.pk if not request.user.is_anonymous else None,
                "offer": offer_pk,
                "picked_color": picked_color,
                "picked_size": picked_size,
                "picked_quantity": picked_quantity,
                "picked_date": picked_date,
                "picked_hour": picked_hour,
            })
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            raise ValidationError(serializer.errors)

    @staticmethod
    def delete(request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        cart_pk = kwargs.get('cart_pk')
        try:
            if request.user.is_anonymous:
                cart_offer = Cart.objects.get(unique_id=unique_id, pk=cart_pk)
            else:
                cart_offer = Cart.objects.get(user=request.user, pk=cart_pk)
            cart_offer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            errors = {"error": ["Cart offer not found."]}
            raise ValidationError(errors)


class GetMyCartListView(APIView, GetMyCartPagination):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        if request.user.is_anonymous:
            cart_offers = Cart.objects.filter(unique_id=unique_id)
        else:
            cart_offers = Cart.objects.filter(user=request.user)
        # Check how many shop ids exist on user cart
        # pk 1 = 2 times
        # pk 2 = 1 time
        # Example : Counter({1: 2, 2: 1})
        # Len = 2
        shop_count = len(Counter(cart_offers.values_list('offer__auth_shop__pk', flat=True)))
        total_price = GetCartPrices().calculate_total_price(cart_offers)
        page = self.paginate_queryset(request=request, queryset=cart_offers)
        if page is not None:
            if request.user.is_anonymous:
                return self.get_paginated_response_unique_id_custom(page, unique_id, shop_count, total_price)
            else:
                return self.get_paginated_response_user_custom(page, request.user, shop_count, total_price)


class GetCartCounterView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        if request.user.is_anonymous:
            cart_counter = Cart.objects.filter(unique_id=unique_id).count()
        else:
            cart_counter = Cart.objects.filter(user=request.user).count()
        data = {
            'cart_counter': cart_counter
        }
        return Response(data=data, status=status.HTTP_200_OK)


class ValidateCartOffersView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get_order_number(unique_id):
        date_time = datetime.now()
        time_stamp = datetime.timestamp(date_time)
        str_time_stamp = str(time_stamp)
        str_time_stamp_seconds = str_time_stamp.split('.')
        timestamp_rnd = str_time_stamp_seconds[0][6:]
        uid = urlsafe_base64_encode(force_bytes(unique_id))
        return '{}-{}'.format(timestamp_rnd, uid[0:3].upper())

    def post(self, request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        seller = request.data.get('shop_pk')
        lot_pks = request.data.get('lot_pks')
        objects = Cart.objects.filter(id__in=lot_pks)
        objects = dict([(obj.id, obj) for obj in objects])
        cart_offers = [objects[id_] for id_ in lot_pks]
        if len(cart_offers) == 0:
            errors = {"error": ["Your cart is empty"]}
            raise ValidationError(errors)
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        order_serializer = BaseOrderSerializer(data={
            'seller': seller,
            'buyer': request.user.pk if not request.user.is_anonymous else None,
            'first_name': first_name,
            'last_name': last_name,
            'note': request.data.get('note'),
            'order_number': self.get_order_number(unique_id) if request.user.is_anonymous
            else self.get_order_number(uuid4()),
            'total_price': GetCartPrices().calculate_total_price(cart_offers),  # includes solder + quantity
        })
        if order_serializer.is_valid():
            order = order_serializer.save()
            # Generate buyer picture
            if request.user.is_anonymous:
                base_generate_user_thumbnail.apply_async((order.pk,), )
            else:
                order.buyer_avatar_thumbnail = request.user.avatar_thumbnail
                order.save()
            address = request.data.get('address', None)
            city = request.data.get('city', None)
            zip_code = request.data.get('zip_code', None)
            country = request.data.get('country', None)
            phone = request.data.get('phone')
            email = request.data.get('email')

            picked_click_and_collect = request.data.get('picked_click_and_collect', False)
            picked_delivery = request.data.get('picked_delivery', False)
            if picked_click_and_collect:
                check_click_and_collect = str(picked_click_and_collect).split(',')
            else:
                check_click_and_collect = False
            if picked_delivery:
                check_picked_delivery = str(picked_delivery).split(',')
            else:
                check_picked_delivery = False

            delivery_pk = request.data.get('delivery_pk', None)
            try:
                delivery = Delivery.objects.get(pk=delivery_pk, offer__auth_shop=seller)
            except Delivery.DoesNotExist:
                delivery = None
            highest_delivery_price = 0
            order_details_valid = False
            order_details_serializer_errors = None

            for index, cart_offer in enumerate(cart_offers):
                delivery_price_count = 0
                if cart_offer.offer.offer_type == 'V':
                    if bool(int(check_picked_delivery[index])) and delivery:
                        delivery_price = delivery.delivery_price
                        if delivery_price > highest_delivery_price:
                            order.highest_delivery_price = delivery_price
                            order.save(update_fields=['highest_delivery_price'])
                            highest_delivery_price = delivery_price
                        delivery_price_count = delivery_price
                picked_click_and_collect = bool(int(check_click_and_collect[index])) if isinstance(
                        check_click_and_collect, list) and cart_offer.offer.offer_type == 'V' else False
                picked_delivery = bool(int(check_picked_delivery[index])) if isinstance(
                        check_picked_delivery, list) and cart_offer.offer.offer_type == 'V' else False
                order_detail_serializer = BaseOrderDetailsSerializer(data={
                    'order': order.pk,
                    'offer': cart_offer.offer.pk,
                    'offer_type': cart_offer.offer.offer_type,
                    'offer_title': cart_offer.offer.title,
                    'offer_price': cart_offer.offer.price,
                    'picked_click_and_collect': picked_click_and_collect,
                    'product_longitude': cart_offer.offer.offer_products.product_longitude
                    if cart_offer.offer.offer_type == 'V' and picked_click_and_collect else None,
                    'product_latitude': cart_offer.offer.offer_products.product_latitude
                    if cart_offer.offer.offer_type == 'V' and picked_click_and_collect else None,
                    'product_address': cart_offer.offer.offer_products.product_address
                    if cart_offer.offer.offer_type == 'V' and picked_click_and_collect else None,
                    'picked_delivery': picked_delivery,
                    # Deliveries data
                    'delivery_price': delivery_price_count,
                    'address': address if picked_delivery else None,
                    'city': city if picked_delivery else None,
                    'zip_code': zip_code if picked_delivery else None,
                    'country': country if picked_delivery else None,
                    'phone': phone if picked_delivery or cart_offer.offer.offer_type == 'S' else None,
                    # end - deliveries data
                    'email': email,
                    'picked_color': cart_offer.picked_color,
                    'picked_size': cart_offer.picked_size,
                    'picked_quantity': cart_offer.picked_quantity if cart_offer.picked_quantity else 1,
                    'picked_date': cart_offer.picked_date,
                    'picked_hour': cart_offer.picked_hour,
                    'service_zone_by': cart_offer.offer.offer_services.service_zone_by
                    if cart_offer.offer.offer_type == 'S' else None,
                    'service_longitude': cart_offer.offer.offer_services.service_longitude
                    if cart_offer.offer.offer_type == 'S' else None,
                    'service_latitude': cart_offer.offer.offer_services.service_latitude
                    if cart_offer.offer.offer_type == 'S' else None,
                    'service_address': cart_offer.offer.offer_services.service_address
                    if cart_offer.offer.offer_type == 'S' else None,
                    'service_km_radius': cart_offer.offer.offer_services.service_km_radius
                    if cart_offer.offer.offer_type == 'S' else None,
                })
                if order_detail_serializer.is_valid():
                    order_details = order_detail_serializer.save()
                    # Generate offer thumbnail
                    base_duplicate_order_offer_image.apply_async((cart_offer.offer.pk, order_details.pk), )
                    order_details_valid = True
                else:
                    order_details_serializer_errors = order_detail_serializer.errors
                    order_details_valid = False
            if order_details_valid:
                cart_offers = Cart.objects.filter(unique_id=unique_id, offer__auth_shop=seller)
                cart_offers.delete()
                user = AuthShop.objects.get(pk=seller).user
                Notifications.objects.create(user=user, type='OR')
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                if order_details_serializer_errors:
                    raise ValidationError(order_details_serializer_errors)
        raise ValidationError(order_serializer.errors)
