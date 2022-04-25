from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from account.models import UserAddress
from offer.base.models import Offers, Delivery, Products, Services, Solder
from cart.base.serializers import BaseCartOfferDetailsSerializer, BaseCartOfferSerializer, \
    BaseCartOfferPutSerializer, BaseCartOfferDeliveriesDetailsSerializer
from cart.base.models import Cart
from cart.base.pagination import GetMyCartPagination
from cart.base.utils import GetCartPrices
from order.base.serializers import BaseNewOrderSerializer, BaseOferDetailsProductSerializer, \
    BaseOfferDetailsServiceSerializer
from datetime import datetime
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
# from random import choice
# from string import ascii_letters, digits


class GetCartOffersView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user_pk = request.user
        offer_pks = kwargs.get('offer_pks')
        offer_pks_list = str(offer_pks).split(',')
        cart_offer = Cart.objects.filter(user=user_pk, offer_id__in=offer_pks_list) \
            .order_by('-created_date', '-updated_date')
        cart_offer_details_serializer = BaseCartOfferDetailsSerializer(cart_offer, many=True)
        return Response(cart_offer_details_serializer.data, status=status.HTTP_200_OK)


class GetCartOffersDeliveriesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user_pk = request.user
        offer_pks = kwargs.get('offer_pks')
        offer_pks_list = str(offer_pks).split(',')
        cart_offer = Cart.objects.filter(user=user_pk, offer_id__in=offer_pks_list) \
            .order_by('-created_date', '-updated_date')
        cart_offer_details_serializer = BaseCartOfferDeliveriesDetailsSerializer(cart_offer, many=True)
        return Response(cart_offer_details_serializer.data, status=status.HTTP_200_OK)


class CartOffersView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user_pk = request.user.pk
        offer_pk = request.data.get('offer_pk')
        picked_color = request.data.get('picked_color', None)
        picked_size = request.data.get('picked_size', None)
        note = request.data.get('note', None)
        picked_quantity = request.data.get('picked_quantity', None)
        picked_date = request.data.get('picked_date', None)
        picked_hour = request.data.get('picked_hour', None)
        try:
            Offers.objects.get(pk=offer_pk, auth_shop__user_id=user_pk)
            data = {
                'errors': "Can't add your own offers to your cart!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except Offers.DoesNotExist:
            try:
                Cart.objects.get(user_id=user_pk, offer_id=offer_pk)
                data = {
                    'errors': "Already in cart!"
                }
                return Response(data=data, status=status.HTTP_200_OK)
            except Cart.DoesNotExist:
                serializer = BaseCartOfferSerializer(data={
                    "user": user_pk,
                    "offer": offer_pk,
                    "note": note,
                    "picked_color": picked_color,
                    "picked_size": picked_size,
                    "picked_quantity": picked_quantity,
                    "picked_date": picked_date,
                    "picked_hour": picked_hour,
                })
                if serializer.is_valid():
                    serializer.save()
                    return Response(data=serializer.data, status=status.HTTP_200_OK)
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(request, *args, **kwargs):
        user_pk = request.user
        cart_pk = request.data.get('cart_pk')
        cart_offer = Cart.objects.get(user=user_pk, pk=cart_pk)
        serializer = BaseCartOfferPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(cart_offer, serializer.validated_data)
            data = {
                'note': serializer.validated_data.get('note'),
                "picked_color": serializer.validated_data.get('picked_color'),
                "picked_size": serializer.validated_data.get('picked_size'),
                "picked_quantity": serializer.validated_data.get('picked_quantity'),
                "picked_date": serializer.validated_data.get('picked_date'),
                "picked_hour": serializer.validated_data.get('picked_hour'),
                "total_price": GetCartPrices().get_offer_price(cart_offer)
            }
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        user = request.user
        cart_pk = kwargs.get('cart_pk')
        try:
            cart_offer = Cart.objects.get(user=user, pk=cart_pk)
            reduced_price = GetCartPrices().get_offer_price(cart_offer)
            cart_offer.delete()
            data = {
                'minus_price': reduced_price
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            data = {'errors': ['Cart offer not found.']}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class GetMyCartListView(APIView, GetMyCartPagination):
    permission_classes = (permissions.IsAuthenticated,)
    page_size = 10

    def get(self, request, *args, **kwargs):
        user_pk = request.user
        cart_offers = Cart.objects.filter(user=user_pk).order_by('-created_date', '-updated_date')
        # Check how many shop ids exist on user cart
        cart_shop_count = cart_offers.values('offer__auth_shop').count()
        total_price = GetCartPrices().calculate_total_price(cart_offers)
        page = self.paginate_queryset(request=request, queryset=cart_offers)
        return self.get_paginated_response_custom(page, cart_shop_count, total_price)


class ValidateCartOffersView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get_offer_price(instance, picked_quantity=1, delivery_price=0):
        try:
            solder = Solder.objects.get(offer=instance.pk)
            # Réduction fix
            if solder.solder_type == 'F':
                offer_price = instance.price - solder.solder_value
            # Réduction Pourcentage
            else:
                offer_price = instance.price - (instance.price * solder.solder_value / 100)
            return (offer_price * picked_quantity) + delivery_price
        except Solder.DoesNotExist:
            return (instance.price * picked_quantity) + delivery_price

    # @staticmethod
    # def random_unique_id(length=15):
    #     letters_digits = ascii_letters + digits
    #     return ''.join(choice(letters_digits) for i in range(length))

    def post(self, request, *args, **kwargs):
        user_pk = request.user
        shop_pk = request.data.get('shop_pk')
        user_address_pk = request.data.get('user_address_pk')
        delivery_pk = request.data.get('delivery_pk')
        cart_offers = Cart.objects.filter(user=user_pk, offer__auth_shop_id=shop_pk) \
            .order_by('-created_date', '-updated_date')
        delivery = Delivery.objects.get(pk=delivery_pk, offer__auth_shop_id=shop_pk)
        user_address = UserAddress.objects.get(user=user_pk, pk=user_address_pk)
        # Means single or multiple products/services from one shop
        if len(cart_offers) == 1:
            for cart_offer in cart_offers:
                date_time = datetime.now()
                time_stamp = datetime.timestamp(date_time)
                str_time_stamp = str(time_stamp)
                str_time_stamp_seconds = str_time_stamp.split('.')
                timestamp_rnd = str_time_stamp_seconds[0][6:]
                uid = urlsafe_base64_encode(force_bytes(request.user.pk))
                # order_date = default auto now
                # order_status = default to confirm
                # my_unique_id = self.random_unique_id()
                order_serializer = BaseNewOrderSerializer(data={
                    'buyer': cart_offer.user.pk,
                    'seller': cart_offer.offer.auth_shop.pk,
                    'order_number': '{}-{}'.format(timestamp_rnd, uid),
                    # 'unique_id': my_unique_id
                })
                if order_serializer.is_valid():
                    order_serializer = order_serializer.save()
                    # Products
                    if cart_offer.offer.offer_type == 'V':
                        product_details = Products.objects.get(offer=cart_offer.offer.pk)

                        order_details_product_serializer = BaseOferDetailsProductSerializer(data={
                            'order': order_serializer.pk,
                            'offer': cart_offer.offer.pk,
                            'title': cart_offer.offer.title,
                            'picked_click_and_collect': request.data.get('picked_click_and_collect', False),
                            'product_longitude': product_details.product_longitude,
                            'product_latitude': product_details.product_latitude,
                            'product_address': product_details.product_address,
                            'picked_delivery': request.data.get('picked_delivery', False),
                            'delivery_city': ", ".join([i.name_fr for i in delivery.delivery_city.all()]),
                            'delivery_price': delivery.delivery_price,
                            'delivery_days': delivery.delivery_days,
                            'first_name': user_address.first_name,
                            'last_name': user_address.last_name,
                            'address': user_address.address,
                            'city': user_address.city.name_fr,
                            'zip_code': user_address.zip_code,
                            'country': user_address.country.name_fr,
                            'phone': user_address.phone,
                            'note': cart_offer.note,
                            'picked_color': cart_offer.picked_color,
                            'picked_size': cart_offer.picked_size,
                            'picked_quantity': cart_offer.picked_quantity,
                            'picked_date': cart_offer.picked_date,
                            'picked_hour': cart_offer.picked_hour,
                            'total_self_price': self.get_offer_price(cart_offer.offer, cart_offer.picked_quantity,
                                                                     delivery.delivery_price),
                        })
                        if order_details_product_serializer.is_valid():
                            order_details_product_serializer.save()
                            return Response(data=order_details_product_serializer.data, status=status.HTTP_200_OK)
                        return Response(order_details_product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    # Services
                    elif cart_offer.offer.offer_type == 'S':
                        service_details = Services.objects.get(offer=cart_offer.offer.pk)
                        order_details_service_serializer = BaseOfferDetailsServiceSerializer(data={
                            'order': order_serializer.pk,
                            'offer': cart_offer.offer.pk,
                            'title': cart_offer.offer.title,
                            'service_zone_by': service_details.service_zone_by,
                            'service_longitude': service_details.service_longitude,
                            'service_latitude': service_details.service_latitude,
                            'service_address': service_details.service_address,
                            'service_km_radius': service_details.service_km_radius,
                            'first_name': user_address.first_name,
                            'last_name': user_address.last_name,
                            'address': user_address.address,
                            'city': user_address.city.name_fr,
                            'zip_code': user_address.zip_code,
                            'country': user_address.country.name_fr,
                            'phone': user_address.phone,
                            'note': cart_offer.note,
                            'picked_date': cart_offer.picked_date,
                            'picked_hour': cart_offer.picked_hour,
                            'total_self_price': self.get_offer_price(cart_offer.offer),
                        })
                        if order_details_service_serializer.is_valid():
                            order_details_service_serializer.save()
                            return Response(data=order_details_service_serializer.data, status=status.HTTP_200_OK)
                        return Response(order_details_service_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Multiple offers / from one store or multiple stores / may include products & services
        else:
            # TODO needs to calculate each one separatly
            for cart_offer in cart_offers:
                date_time = datetime.now()
                time_stamp = datetime.timestamp(date_time)
                str_time_stamp = str(time_stamp)
                str_time_stamp_seconds = str_time_stamp.split('.')
                timestamp_rnd = str_time_stamp_seconds[0][6:]
                uid = urlsafe_base64_encode(force_bytes(request.user.pk))
                # order_date = default auto now
                # order_status = default to confirm
                # my_unique_id = self.random_unique_id()
                order_serializer = BaseNewOrderSerializer(data={
                    'buer': cart_offer.user,
                    'seller': cart_offer.offer.auth_shop,
                    'order_number': '{}-{}'.format(timestamp_rnd, uid),
                    # 'unique_id': my_unique_id
                })
                if order_serializer.is_valid():
                    order_serializer = order_serializer.save()
                    if cart_offer.offer.offer_type == 'V':
                        product_details = Products.objects.get(offer=cart_offer.offer.pk)
                        order_details_product_serializer = BaseOferDetailsProductSerializer(data={
                            'order': order_serializer.pk,
                            'offer': cart_offer.offer.pk,
                            'title': cart_offer.offer.title,
                            'picked_click_and_collect': request.data.get('picked_click_and_collect'),
                            'product_longitude': product_details.product_longitude,
                            'product_latitude': product_details.product_latitude,
                            'product_address': product_details.product_address,
                            'picked_delivery': request.data.get('picked_delivery'),
                            'delivery_city': ", ".join([i.name_fr for i in delivery.delivery_city.all()]),
                            'delivery_price': delivery.delivery_price,
                            'delivery_days': delivery.delivery_days,
                            'first_name': user_address.first_name,
                            'last_name': user_address.last_name,
                            'address': user_address.address,
                            'city': user_address.city.name_fr,
                            'zip_code': user_address.zip_code,
                            'country': user_address.country.name_fr,
                            'phone': user_address.phone,
                            'note': cart_offer.note,
                            'picked_color': cart_offer.picked_color,
                            'picked_size': cart_offer.picked_size,
                            'picked_quantity': cart_offer.picked_quantity,
                            'picked_date': cart_offer.picked_date,
                            'picked_hour': cart_offer.picked_hour,
                            'total_self_price': self.get_offer_price(cart_offer.offer),
                        }, many=True)
                        if order_details_product_serializer.is_valid():
                            order_details_product_serializer.save()
                    elif cart_offer.offer.offer_type == 'S':
                        service_details = Services.objects.get(offer=cart_offer.offer.pk)
                        order_details_service_serializer = BaseOfferDetailsServiceSerializer(data={
                            'order': order_serializer.pk,
                            'offer': cart_offer.offer.pk,
                            'title': cart_offer.offer.title,
                            'service_zone_by': service_details.service_zone_by,
                            'service_longitude': service_details.service_longitude,
                            'service_latitude': service_details.service_latitude,
                            'service_address': service_details.service_address,
                            'service_km_radius': service_details.service_km_radius,
                            'first_name': user_address.first_name,
                            'last_name': user_address.last_name,
                            'address': user_address.address,
                            'city': user_address.city.name_fr,
                            'zip_code': user_address.zip_code,
                            'country': user_address.country.name_fr,
                            'phone': user_address.phone,
                            'note': cart_offer.note,
                            'picked_date': cart_offer.picked_date,
                            'picked_hour': cart_offer.picked_hour,
                            'total_self_price': self.get_offer_price(cart_offer.offer),
                        }, many=True)
                        if order_details_service_serializer.is_valid():
                            order_details_service_serializer.save()
