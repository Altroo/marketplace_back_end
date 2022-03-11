from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from auth_shop.base.serializers import BaseShopSerializer, BaseShopAvatarPutSerializer, \
    BaseShopNamePutSerializer, BaseShopBioPutSerializer, BaseShopAvailabilityPutSerializer, \
    BaseShopContactPutSerializer, BaseShopAddressPutSerializer, BaseShopColorPutSerializer, \
    BaseShopFontPutSerializer, BaseGETShopInfoSerializer, BaseShopTelPutSerializer, \
    BaseShopWtspPutSerializer
from os import path, remove
from uuid import uuid4
from urllib.parse import quote_plus
from django.core.exceptions import SuspiciousFileOperation
from auth_shop.base.tasks import base_generate_avatar_thumbnail
from celery import current_app
from auth_shop.base.models import AuthShop, AuthShopDays
from temp_shop.base.models import TempShop
from temp_offer.base.models import TempOffers, TempSolder, TempDelivery
from offer.base.models import Offers, Products, Services, Solder, Delivery


class ShopView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def post(request, *args, **kwargs):
        shop_name = request.data.get('shop_name')
        qaryb_url = quote_plus(shop_name)
        unique_id = uuid4()
        serializer = BaseShopSerializer(data={
            'user': request.user,
            'shop_name': shop_name,
            'avatar': request.data.get('avatar'),
            'color_code': request.data.get('color_code'),
            'bg_color_code': request.data.get('bg_color_code'),
            'font_name': request.data.get('font_name'),
            'qaryb_link': 'https://qaryb.com/' + qaryb_url + str(unique_id),
        })
        if serializer.is_valid():
            shop = serializer.save()
            shop.save()
            data = {
                'unique_id': unique_id,
                'shop_name': shop.shop_name,
                'avatar': shop.get_absolute_avatar_img,
                'color_code': shop.color_code,
                'bg_color_code': shop.bg_color_code,
                'font_name': shop.font_name
            }
            # Generate thumbnail
            base_generate_avatar_thumbnail.apply_async((shop.pk, 'AuthShop'), )
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get(request, *args, **kwargs):
        auth_shop_pk = kwargs.get('auth_shop_pk')
        try:
            shop = AuthShop.objects.get(pk=auth_shop_pk)
            shop_details_serializer = BaseGETShopInfoSerializer(shop)
            return Response(shop_details_serializer.data, status=status.HTTP_200_OK)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class TempShopToAuthShopView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        user = request.user
        try:
            temp_shop = TempShop.objects.get(unique_id=unique_id)
            task_id = temp_shop.task_id
            # revoke 24h periodic task
            current_app.control.revoke(task_id, terminate=True, signal='SIGKILL')
            # transfer temp shop data
            auth_shop = AuthShop.objects.create(
                user=user,
                shop_name=temp_shop.shop_name,
                avatar=temp_shop.avatar,
                avatar_thumbnail=temp_shop.avatar_thumbnail,
                color_code=temp_shop.color_code,
                bg_color_code=temp_shop.bg_color_code,
                font_name=temp_shop.font_name,
                bio=temp_shop.bio,
                morning_hour_from=temp_shop.morning_hour_from,
                morning_hour_to=temp_shop.morning_hour_to,
                afternoon_hour_from=temp_shop.afternoon_hour_from,
                afternoon_hour_to=temp_shop.afternoon_hour_to,
                phone=temp_shop.phone,
                contact_email=temp_shop.contact_email,
                website_link=temp_shop.website_link,
                facebook_link=temp_shop.facebook_link,
                twitter_link=temp_shop.twitter_link,
                instagram_link=temp_shop.instagram_link,
                whatsapp=temp_shop.whatsapp,
                zone_by=temp_shop.zone_by,
                longitude=temp_shop.longitude,
                latitude=temp_shop.latitude,
                address_name=temp_shop.address_name,
                km_radius=temp_shop.km_radius,
                qaryb_link=temp_shop.qaryb_link
            )
            auth_shop.save()
            # Auth shop opening days
            opening_days = temp_shop.opening_days.all()
            for opening_day in opening_days:
                auth_shop.opening_days.add(opening_day.pk)
            # Offers
            temp_offers = TempOffers.objects.filter(temp_shop=temp_shop.pk) \
                .select_related('temp_offer_products') \
                .select_related('temp_offer_services') \
                .select_related('temp_offer_solder') \
                .prefetch_related('temp_offer_delivery')
            for temp_offer in temp_offers:
                offer = Offers.objects.create(
                    auth_shop=auth_shop,
                    offer_type=temp_offer.offer_type,
                    # Offer categories
                    title=temp_offer.title,
                    # May lead to a db error picture not found
                    picture_1=temp_offer.picture_1,
                    picture_2=temp_offer.picture_2,
                    picture_3=temp_offer.picture_3,
                    picture_4=temp_offer.picture_4,
                    picture_1_thumbnail=temp_offer.picture_1_thumbnail,
                    picture_2_thumbnail=temp_offer.picture_2_thumbnail,
                    picture_3_thumbnail=temp_offer.picture_3_thumbnail,
                    picture_4_thumbnail=temp_offer.picture_4_thumbnail,
                    description=temp_offer.description,
                    # For whom
                    price=temp_offer.price,
                )
                offer.save()
                temp_categories = temp_offer.offer_categories.all()
                for temp_categorie in temp_categories:
                    offer.offer_categories.add(temp_categorie.pk)
                for_whoms = temp_offer.for_whom.all()
                for for_whom in for_whoms:
                    offer.for_whom.add(for_whom.pk)
                if temp_offer.offer_type == 'V':
                    product = Products.objects.create(
                        offer=offer,
                        # product_colors
                        # product_sizes
                        product_quantity=temp_offer.temp_offer_products.product_quantity,
                        product_price_by=temp_offer.temp_offer_products.product_price_by,
                        product_longitude=temp_offer.temp_offer_products.product_longitude,
                        product_latitude=temp_offer.temp_offer_products.product_latitude,
                        product_address=temp_offer.temp_offer_products.product_address
                    )
                    product.save()
                    # product_colors
                    product_colors = temp_offer.temp_offer_products.product_colors.all()
                    for product_color in product_colors:
                        product.product_colors.add(product_color.pk)
                    # product_sizes
                    product_sizes = temp_offer.temp_offer_products.product_sizes.all()
                    for product_size in product_sizes:
                        product.product_sizes.add(product_size.pk)
                elif temp_offer.offer_type == 'S':
                    service = Services.objects.create(
                        offer=offer,
                        # service_availability_days
                        service_morning_hour_from=temp_offer.temp_offer_services.service_morning_hour_from,
                        service_morning_hour_to=temp_offer.temp_offer_services.service_morning_hour_to,
                        service_afternoon_hour_from=temp_offer.temp_offer_services.service_afternoon_hour_from,
                        service_afternoon_hour_to=temp_offer.temp_offer_services.service_afternoon_hour_to,
                        service_zone_by=temp_offer.temp_offer_services.service_zone_by,
                        service_price_by=temp_offer.temp_offer_services.service_price_by,
                        service_longitude=temp_offer.temp_offer_services.service_longitude,
                        service_latitude=temp_offer.temp_offer_services.service_latitude,
                        service_address=temp_offer.temp_offer_services.service_address,
                        service_km_radius=temp_offer.temp_offer_services.service_km_radius
                    )
                    service.save()
                    # service_availability_days
                    service_availability_days = temp_offer.temp_offer_services.service_availability_days.all()
                    for service_availability_day in service_availability_days:
                        service.service_availability_days.add(service_availability_day.pk)
                # Transfer solder
                try:
                    temp_solder = TempSolder.objects.get(temp_offer=temp_offer.pk)
                    solder = Solder.objects.create(
                        offer=offer.pk,
                        solder_type=temp_solder.temp_solder_type,
                        solder_value=temp_solder.temp_solder_value
                    )
                    solder.save()
                except TempSolder.DoesNotExist:
                    continue
                # Transfer deliveries
                try:
                    temp_deliveries = TempDelivery.objects.get(temp_offer=temp_offer.pk)
                    delivery = Delivery.objects.create(
                        offer=offer.pk,
                        delivery_city_1=temp_deliveries.temp_delivery_city_1,
                        delivery_price_1=temp_deliveries.temp_delivery_price_1,
                        delivery_days_1=temp_deliveries.temp_delivery_days_1,
                        delivery_city_2=temp_deliveries.temp_delivery_city_2,
                        delivery_price_2=temp_deliveries.temp_delivery_price_2,
                        delivery_days_2=temp_deliveries.temp_delivery_days_2,
                        delivery_city_3=temp_deliveries.temp_delivery_city_3,
                        delivery_price_3=temp_deliveries.temp_delivery_price_3,
                        delivery_days_3=temp_deliveries.temp_delivery_days_3,
                    )
                    delivery.save()
                except TempDelivery.DoesNotExist:
                    continue
            temp_shop.delete()
            data = {
                'response': 'Temp shop data transfered into Auth shop!'
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except TempShop.DoesNotExist:
            data = {'errors': ['User temp shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopAvatarPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('auth_shop_pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopAvatarPutSerializer(data=request.data)
        if serializer.is_valid():
            if shop.avatar:
                try:
                    remove(shop.avatar.path)
                except (ValueError, SuspiciousFileOperation, FileNotFoundError):
                    pass
            if shop.avatar_thumbnail:
                try:
                    remove(shop.avatar_thumbnail.path)
                except (ValueError, SuspiciousFileOperation, FileNotFoundError):
                    pass
            new_avatar = serializer.update(shop, serializer.validated_data)
            # Generate new avatar thumbnail
            base_generate_avatar_thumbnail.apply_async((new_avatar.pk, 'AuthShop'), )
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopNamePutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('auth_shop_pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopNamePutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopBioPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('auth_shop_pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopBioPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopAvailabilityPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('auth_shop_pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopAvailabilityPutSerializer(data={
            'morning_hour_from': request.data.get('morning_hour_from'),
            'morning_hour_to': request.data.get('morning_hour_to'),
            'afternoon_hour_from': request.data.get('afternoon_hour_from'),
            'afternoon_hour_to': request.data.get('afternoon_hour_to'),
        })
        if serializer.is_valid():
            new_availability = serializer.update(shop, serializer.validated_data)
            opening_days = str(request.data.get('opening_days')).split(',')
            opening_days = AuthShopDays.objects.filter(code_day__in=opening_days)
            new_availability.opening_days.clear()
            for day in opening_days:
                new_availability.opening_days.add(day.pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopContactPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('auth_shop_pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopContactPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopTelPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('auth_shop_pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopTelPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(shop, serializer.validated_data)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopWtspPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('auth_shop_pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopWtspPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(shop, serializer.validated_data)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopAddressPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('auth_shop_pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopAddressPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopColorPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('auth_shop_pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopColorPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopFontPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('auth_shop_pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopFontPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
