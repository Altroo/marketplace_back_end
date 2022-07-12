from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from account.models import UserAddress
from offers.models import Offers, Delivery, Products, Services, Solder
from cart.base.serializers import BaseCartOfferSerializer, BaseCartOfferPutSerializer, \
    BaseNewOrderSerializer, BaseOferDetailsProductSerializer, \
    BaseOfferDetailsServiceSerializer, BaseNewOrderHighestDeliveryPrice, \
    BaseGetServicesCoordinatesSerializer
from cart.models import Cart
from cart.base.pagination import GetMyCartPagination, GetCartOffersDetailsPagination
from cart.base.utils import GetCartPrices
from datetime import datetime
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from order.base.tasks import base_duplicate_order_images
from collections import Counter


# Mobile only not used
# class GetCartOffersView(APIView):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     @staticmethod
#     def get(request, *args, **kwargs):
#         user = request.user
#         # offer_pks = kwargs.get('offer_pks')
#         shop_pk = kwargs.get('shop_pk')
#         # offer_pks_list = str(offer_pks).split(',')
#         # cart_offer = Cart.objects.filter(user=user_pk, offer_id__in=offer_pks_list) \
#         #     .order_by('-created_date', '-updated_date')
#         cart_offer = Cart.objects.filter(user=user, offer__auth_shop=shop_pk)
#         .order_by('-created_date', '-updated_date')
#         cart_offer_details_serializer = BaseCartDetailsListSerializer(cart_offer, many=True)
#         return Response(cart_offer_details_serializer.data, status=status.HTTP_200_OK)

class GetCartOffersDetailsView(APIView, GetCartOffersDetailsPagination):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        shop_pk = kwargs.get('shop_pk')
        cart_offers = Cart.objects.filter(user=user, offer__auth_shop=shop_pk) \
            .order_by('-created_date', '-updated_date')
        total_price = GetCartPrices().calculate_total_price(cart_offers)
        page = self.paginate_queryset(request=request, queryset=cart_offers)
        if page is not None:
            return self.get_paginated_response_custom(user, shop_pk, total_price)


# class GetCartOffersDetailsView(APIView):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     @staticmethod
#     def get(request, *args, **kwargs):
#         user = request.user
#         shop_pk = kwargs.get('shop_pk')
#         cart_offer = Cart.objects.filter(user=user, offer__auth_shop=shop_pk).order_by('-created_date',
#         '-updated_date')
#         serializer = BaseCartOffersDetailsSerializer(cart_offer, many=True)
#         print(type(serializer.data))
#         print(serializer.data)
#         result = serializer.data.sort(reverse=True, key=lambda key_needed: key_needed['offer_details'])
#         return Response(result, status=status.HTTP_200_OK)


class CartOffersView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user_pk = request.user.pk
        offer_pk = request.data.get('offer_pk')
        picked_color = request.data.get('picked_color', None)
        picked_size = request.data.get('picked_size', None)
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
    def patch(request, *args, **kwargs):
        user_pk = request.user
        cart_pk = request.data.get('cart_pk')
        cart_offer = Cart.objects.get(user=user_pk, pk=cart_pk)
        serializer = BaseCartOfferPutSerializer(cart_offer, data=request.data, partial=True)
        if serializer.is_valid():
            # serializer.update(cart_offer, serializer.validated_data)
            serializer.save()
            # data = {
            #     "picked_color": serializer.validated_data.get('picked_color'),
            #     "picked_size": serializer.validated_data.get('picked_size'),
            #     "picked_quantity": serializer.validated_data.get('picked_quantity'),
            #     "picked_date": serializer.validated_data.get('picked_date'),
            #     "picked_hour": serializer.validated_data.get('picked_hour'),
            #     "total_price": GetCartPrices().get_offer_price(cart_offer)
            # }
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Return new total price
    @staticmethod
    def delete(request, *args, **kwargs):
        user = request.user
        cart_pk = kwargs.get('cart_pk')
        try:
            cart_offer = Cart.objects.get(user=user, pk=cart_pk)
            reduced_price = GetCartPrices().get_offer_price(cart_offer)
            cart_offer.delete()
            data = {
                'total_price': reduced_price
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            data = {'errors': ['Cart offer not found.']}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


# class GetMyCartListView(APIView, GetMyCartPagination):
#     permission_classes = (permissions.IsAuthenticated,)
#     page_size = 10
#
#     def get(self, request, *args, **kwargs):
#         user_pk = request.user
#         cart_offers = Cart.objects.filter(user=user_pk).order_by('-created_date', '-updated_date')
#         # Check how many shop ids exist on user cart
#         cart_shop_count = cart_offers.values('offer__auth_shop').count()
#         total_price = GetCartPrices().calculate_total_price(cart_offers)
#         page = self.paginate_queryset(request=request, queryset=cart_offers)
#         if page is not None:
#             return self.get_paginated_response_custom(page, cart_shop_count, total_price)


class GetMyCartListView(APIView, GetMyCartPagination):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        cart_offers = Cart.objects.filter(user=user).order_by('-created_date', '-updated_date')
        # Check how many shop ids exist on user cart
        # pk 1 = 2 times
        # pk 2 = 1 time
        # Example : Counter({1: 2, 2: 1})
        # Len = 2
        shop_count = len(Counter(cart_offers.values_list('offer__auth_shop__pk', flat=True)))
        total_price = GetCartPrices().calculate_total_price(cart_offers)
        page = self.paginate_queryset(request=request, queryset=cart_offers)
        if page is not None:
            return self.get_paginated_response_custom(page, shop_count, total_price)


class ValidateCartOffersView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get_offer_price(instance, picked_quantity=1, delivery_price=0, solder=None):
        if solder is not None:
            # Réduction fix
            if solder.solder_type == 'F':
                offer_price = instance.price - solder.solder_value
            # Réduction Pourcentage
            else:
                offer_price = instance.price - (instance.price * solder.solder_value / 100)
            return (offer_price * picked_quantity) + delivery_price
        return (instance.price * picked_quantity) + delivery_price

    def post(self, request, *args, **kwargs):
        user = request.user
        shop_pk = request.data.get('shop_pk')
        note = request.data.get('note')
        cart_offers = Cart.objects.filter(user=user, offer__auth_shop_id=shop_pk) \
            .order_by('-created_date', '-updated_date')
        if len(cart_offers) == 0:
            data = {
                'errors': "Your cart is empty"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        # Means single or multiple products/services from one shop
        cart_offer = cart_offers[0]
        date_time = datetime.now()
        time_stamp = datetime.timestamp(date_time)
        str_time_stamp = str(time_stamp)
        str_time_stamp_seconds = str_time_stamp.split('.')
        timestamp_rnd = str_time_stamp_seconds[0][6:]
        uid = urlsafe_base64_encode(force_bytes(request.user.pk))
        # order_date = default auto now
        # order_status = default to confirm
        # my_unique_id = self.random_unique_id()
        buyer_pk = cart_offer.user.pk
        seller_pk = cart_offer.offer.auth_shop.pk
        offer_pk = cart_offer.offer.pk
        if len(cart_offers) == 1:
            # Since len == 1 we take the first object
            highest_delivery_price = 0
            order_serializer = BaseNewOrderSerializer(data={
                'buyer': buyer_pk,
                'seller': seller_pk,
                'first_name': cart_offer.user.first_name,
                'last_name': cart_offer.user.last_name,
                'buyer_avatar_thumbnail': None,
                'shop_name': cart_offer.offer.auth_shop.shop_name,
                'seller_avatar_thumbnail': None,
                'note': note,
                'order_number': '{}-{}'.format(timestamp_rnd, uid),
                'highest_delivery_price': highest_delivery_price,
            })
            if order_serializer.is_valid():
                order_serializer = order_serializer.save()
                try:
                    solder = Solder.objects.get(offer=cart_offer.offer.pk)
                except Solder.DoesNotExist:
                    solder = None
                # Products
                if cart_offer.offer.offer_type == 'V':
                    delivery_pk = request.data.get('delivery_pk')
                    delivery = Delivery.objects.get(pk=delivery_pk, offer__auth_shop_id=shop_pk)
                    user_address_pk = request.data.get('user_address_pk')
                    picked_click_and_collect = request.data.get('picked_click_and_collect', False)
                    picked_delivery = request.data.get('picked_delivery', False)
                    user_address = UserAddress.objects.get(user=user, pk=user_address_pk)
                    product_details = Products.objects.get(offer=cart_offer.offer.pk)
                    delivery_price = 0
                    if picked_delivery and picked_delivery == str(1):
                        order_updater = BaseNewOrderHighestDeliveryPrice(data={
                            'highest_delivery_price': delivery.delivery_price
                        })
                        if order_updater.is_valid():
                            order_updater.update(order_serializer, order_updater.validated_data)
                        delivery_price = delivery.delivery_price
                        total_self_price = self.get_offer_price(cart_offer.offer, cart_offer.picked_quantity,
                                                                0, solder)
                    if picked_click_and_collect and picked_click_and_collect == str(1):
                        total_self_price = self.get_offer_price(cart_offer.offer, cart_offer.picked_quantity,
                                                                0, solder)
                    if not picked_delivery and not picked_click_and_collect:
                        data = {
                            'errors': "You need to pick a delivery or click & collect"
                        }
                        order_serializer.delete()
                        return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
                    order_details_product_serializer = BaseOferDetailsProductSerializer(data={
                        'order': order_serializer.pk,
                        # Offer Fallback if deleted
                        'offer_type': cart_offer.offer.offer_type,
                        'title': cart_offer.offer.title,
                        'offer_thumbnail': None,
                        'picked_click_and_collect': picked_click_and_collect,
                        'product_longitude': product_details.product_longitude,
                        'product_latitude': product_details.product_latitude,
                        'product_address': product_details.product_address,
                        'picked_delivery': picked_delivery,
                        'delivery_price': delivery_price,
                        'first_name': user_address.first_name,
                        'last_name': user_address.last_name,
                        'address': user_address.address,
                        'city': user_address.city.name_fr,
                        'zip_code': user_address.zip_code,
                        'country': user_address.country.name_fr,
                        'phone': user_address.phone,
                        'email': user_address.email,
                        'picked_color': cart_offer.picked_color,
                        'picked_size': cart_offer.picked_size,
                        'picked_quantity': cart_offer.picked_quantity,
                        # Handled by the
                        'total_self_price': total_self_price,
                    })
                    if order_details_product_serializer.is_valid():
                        order_details_product_serializer.save()
                        # Duplicate pictures for buyer avatar & seller avatar & offer thumbnail
                        base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                 'buyer_avatar_thumbnail'), )
                        base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                 'seller_avatar_thumbnail'), )
                        base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                 'offer_thumbnail'), )
                        return Response(data=order_details_product_serializer.data, status=status.HTTP_200_OK)
                    return Response(order_details_product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                # Services
                elif cart_offer.offer.offer_type == 'S':
                    service_details = Services.objects.get(offer=cart_offer.offer.pk)
                    first_name = request.data.get('first_name')
                    last_name = request.data.get('last_name')
                    phone = request.data.get('phone')
                    email = request.data.get('email')
                    order_details_service_serializer = BaseOfferDetailsServiceSerializer(data={
                        'order': order_serializer.pk,
                        # Offer Fallback if deleted
                        'offer_type': cart_offer.offer.offer_type,
                        'title': cart_offer.offer.title,
                        'offer_thumbnail': None,
                        'service_zone_by': service_details.service_zone_by,
                        'service_longitude': service_details.service_longitude,
                        'service_latitude': service_details.service_latitude,
                        'service_address': service_details.service_address,
                        'service_km_radius': service_details.service_km_radius,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': phone,
                        'email': email,
                        'picked_date': cart_offer.picked_date,
                        'picked_hour': cart_offer.picked_hour,
                        # Service doesn't have quantity or delivery price, but it can have solder
                        'total_self_price': self.get_offer_price(instance=cart_offer.offer, solder=solder),
                    })
                    if order_details_service_serializer.is_valid():
                        order_details_service_serializer.save()
                        # Override old phone in user model.
                        user.phone = phone
                        user.save()
                        # Duplicate pictures for buyer avatar & seller avatar & offer thumbnail
                        base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                 'buyer_avatar_thumbnail'), )
                        base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                 'seller_avatar_thumbnail'), )
                        base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                 'offer_thumbnail'), )
                        return Response(data=order_details_service_serializer.data, status=status.HTTP_200_OK)
                    return Response(order_details_service_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Multiple offers from one store / may include products & services
        else:
            # Since len > 1 we take all objects
            order_valid = False
            highest_delivery_price = 0
            order_serializer = BaseNewOrderSerializer(data={
                'buyer': buyer_pk,
                'seller': seller_pk,
                'first_name': cart_offers[0].user.first_name,
                'last_name': cart_offers[0].user.last_name,
                'buyer_avatar_thumbnail': None,
                'shop_name': cart_offers[0].offer.auth_shop.shop_name,
                'seller_avatar_thumbnail': None,
                'note': note,
                'order_number': '{}-{}'.format(timestamp_rnd, uid),
                'highest_delivery_price': highest_delivery_price,
            })
            if order_serializer.is_valid():
                order_serializer = order_serializer.save()
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
                for cart_offer in enumerate(cart_offers):
                    try:
                        solder = Solder.objects.get(offer=cart_offer[1].offer.pk)
                    except Solder.DoesNotExist:
                        solder = None
                    # Product
                    if cart_offer[1].offer.offer_type == 'V':
                        delivery_pk = request.data.get('delivery_pk')
                        delivery = Delivery.objects.get(pk=delivery_pk, offer__auth_shop_id=shop_pk)
                        product_details = Products.objects.get(offer=cart_offer[1].offer.pk)
                        user_address_pk = request.data.get('user_address_pk')
                        user_address = UserAddress.objects.get(user=user, pk=user_address_pk)
                        delivery_price = 0
                        if check_picked_delivery or check_click_and_collect:
                            if check_picked_delivery:
                                if check_picked_delivery[cart_offer[0]] == str(1):
                                    if delivery.delivery_price > highest_delivery_price:
                                        order_updater = BaseNewOrderHighestDeliveryPrice(
                                            data={'highest_delivery_price': delivery.delivery_price})
                                        if order_updater.is_valid():
                                            order_updater.update(order_serializer, order_updater.validated_data)
                                        highest_delivery_price = delivery.delivery_price
                                    delivery_price = delivery.delivery_price
                                    total_self_price = self.get_offer_price(cart_offer[1].offer,
                                                                            cart_offer[1].picked_quantity, 0, solder)
                            if check_click_and_collect:
                                if check_click_and_collect[cart_offer[0]] == str(1):
                                    total_self_price = self.get_offer_price(cart_offer[1].offer,
                                                                            cart_offer[1].picked_quantity,
                                                                            0, solder)
                        if not check_picked_delivery and not check_click_and_collect:
                            data = {
                                'errors': "You need to pick a delivery or click & collect"
                            }
                            order_serializer.delete()
                            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
                        order_details_product_serializer = BaseOferDetailsProductSerializer(data={
                            'order': order_serializer.pk,
                            'offer_type': cart_offer[1].offer.offer_type,
                            'title': cart_offer[1].offer.title,
                            'offer_thumbnail': None,
                            'picked_click_and_collect': check_click_and_collect[cart_offer[0]],
                            'product_longitude': product_details.product_longitude,
                            'product_latitude': product_details.product_latitude,
                            'product_address': product_details.product_address,
                            'picked_delivery': check_picked_delivery[cart_offer[0]],
                            'delivery_price': delivery_price,
                            'first_name': user_address.first_name,
                            'last_name': user_address.last_name,
                            'address': user_address.address,
                            'city': user_address.city.name_fr,
                            'zip_code': user_address.zip_code,
                            'country': user_address.country.name_fr,
                            'phone': user_address.phone,
                            'email': user_address.email,
                            'picked_color': cart_offer[1].picked_color,
                            'picked_size': cart_offer[1].picked_size,
                            'picked_quantity': cart_offer[1].picked_quantity,
                            'total_self_price': total_self_price,
                        })
                        if order_details_product_serializer.is_valid():
                            order_details_product_serializer.save()
                            # Duplicate pictures for buyer avatar & seller avatar & offer thumbnail
                            base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                     'buyer_avatar_thumbnail'), )
                            base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                     'seller_avatar_thumbnail'), )
                            base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                     'offer_thumbnail'), )
                            order_valid = True
                        else:
                            return Response(order_details_product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    # Service
                    elif cart_offer[1].offer.offer_type == 'S':
                        first_name = request.data.get('first_name')
                        last_name = request.data.get('last_name')
                        phone = request.data.get('phone')
                        email = request.data.get('email')
                        service_details = Services.objects.get(offer=cart_offer[1].offer.pk)
                        order_details_service_serializer = BaseOfferDetailsServiceSerializer(data={
                            'order': order_serializer.pk,
                            'offer_type': cart_offer[1].offer.offer_type,
                            'title': cart_offer[1].offer.title,
                            'offer_thumbnail': None,
                            'service_zone_by': service_details.service_zone_by,
                            'service_longitude': service_details.service_longitude,
                            'service_latitude': service_details.service_latitude,
                            'service_address': service_details.service_address,
                            'service_km_radius': service_details.service_km_radius,
                            'first_name': first_name,
                            'last_name': last_name,
                            'phone': phone,
                            'email': email,
                            'picked_date': cart_offer[1].picked_date,
                            'picked_hour': cart_offer[1].picked_hour,
                            # Service doesn't have quantity or delivery price, but it can have solder
                            'total_self_price': self.get_offer_price(instance=cart_offer[1].offer, solder=solder),
                        })
                        if order_details_service_serializer.is_valid():
                            order_details_service_serializer.save()
                            # Override old phone in user model.
                            user.phone = phone
                            user.save()
                            # Duplicate pictures for buyer avatar & seller avatar & offer thumbnail
                            base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                     'buyer_avatar_thumbnail'), )
                            base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                     'seller_avatar_thumbnail'), )
                            base_duplicate_order_images.apply_async((buyer_pk, seller_pk, offer_pk,
                                                                     'offer_thumbnail'), )
                            order_valid = True
                        else:
                            return Response(order_details_service_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if order_valid:
                return Response(status=status.HTTP_200_OK)


class GetServicesCoordinates(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        services_coordinates = BaseGetServicesCoordinatesSerializer(user)
        return Response(services_coordinates.data, status=status.HTTP_200_OK)
