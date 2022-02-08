from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from temp_shop.base.serializers import BaseTempShopSerializer, BaseTempShopAvatarPutSerializer, \
    BaseTempShopNamePutSerializer, BaseTempShopBioPutSerializer, BaseTempShopAvailabilityPutSerializer, \
    BaseTempShopContactPutSerializer, BaseTempShopAddressPutSerializer, BaseTempShopColorPutSerializer, \
    BaseTempShopFontPutSerializer
from os import rename, path, remove
from Qaryb_API_new.settings import USER_IMAGES_BASE_NAME, IMAGES_ROOT_NAME
from uuid import uuid4
from urllib.parse import quote_plus
from random import choice
from string import ascii_letters, digits
from datetime import datetime, timedelta
from temp_shop.base.tasks import base_start_deleting_expired_shops
from temp_shop.base.models import TempShop
from django.core.exceptions import SuspiciousFileOperation


class TempShopView(APIView):
    permission_classes = (permissions.AllowAny,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def random_unique_id(length=15):
        letters_digits = ascii_letters + digits
        return ''.join(choice(letters_digits) for i in range(length))

    def post(self, request, *args, **kwargs):
        shop_name = request.data.get('shop_name')
        qaryb_url = quote_plus(shop_name)
        unique_id = uuid4()
        serializer = BaseTempShopSerializer(data={
            'shop_name': shop_name,
            'avatar': request.data.get('avatar'),
            'color_code': request.data.get('color_code'),
            'font_name': request.data.get('font_name'),
            'bio': request.data.get('bio'),
            'opening_days': request.data.get('opening_days'),
            'morning_hour_from': request.data.get('morning_hour_from'),
            'morning_hour_to': request.data.get('morning_hour_to'),
            'afternoon_hour_from': request.data.get('afternoon_hour_from'),
            'afternoon_hour_to': request.data.get('afternoon_hour_to'),
            'phone': request.data.get('phone'),
            'contact_email': request.data.get('contact_email'),
            'website_link': request.data.get('website_link'),
            'facebook_link': request.data.get('facebook_link'),
            'twitter_link': request.data.get('twitter_link'),
            'instagram_link': request.data.get('instagram_link'),
            'whatsapp': request.data.get('whatsapp'),
            'zone_by': request.data.get('zone_by'),
            'longitude': request.data.get('longitude'),
            'latitude': request.data.get('latitude'),
            'address_name': request.data.get('address_name'),
            'km_radius': request.data.get('km_radius'),
            # TODO Remove unique_id
            'qaryb_link': 'https://qaryb.com/' + qaryb_url + str(unique_id),
            'unique_id': str(unique_id),
        })
        if serializer.is_valid():
            temp_shop = serializer.save()
            if temp_shop.avatar:
                avatar_name, avatar_extension = path.splitext(str(temp_shop.avatar))
                avatar_id_name = str(uuid4()) + str(avatar_extension)
                try:
                    rename(self.parent_file_dir + IMAGES_ROOT_NAME + 'media/' +
                           avatar_name + avatar_extension,
                           self.parent_file_dir + USER_IMAGES_BASE_NAME + '/' + avatar_id_name)
                except FileNotFoundError:
                    pass
                    # data = {'errors': [err.strerror, err.filename, err.filename2]}
                    # return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
                temp_shop.avatar = USER_IMAGES_BASE_NAME + '/' + avatar_id_name
                temp_shop.save()
            data = {
                'unique_id': unique_id,
            }
            shift = datetime.utcnow() + timedelta(hours=24)
            base_start_deleting_expired_shops.apply_async((temp_shop.pk,), eta=shift)
            return Response(data=data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TempShopAvatarPutView(APIView):
    permission_classes = (permissions.AllowAny,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    def put(self, request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        temp_shop = TempShop.objects.get(unique_id=unique_id)
        serializer = BaseTempShopAvatarPutSerializer(data=request.data)
        if serializer.is_valid():
            if temp_shop.avatar:
                try:
                    remove(str(self.parent_file_dir) + '/' + str(temp_shop.avatar))
                except (ValueError, SuspiciousFileOperation, FileNotFoundError):
                    pass
            instance = serializer.update(temp_shop, serializer.validated_data)
            avatar_name, avatar_extension = path.splitext(str(instance.avatar))
            avatar_id_name = str(uuid4()) + str(avatar_extension)
            try:
                rename(self.parent_file_dir + IMAGES_ROOT_NAME + 'media/' +
                       avatar_name + avatar_extension,
                       self.parent_file_dir + USER_IMAGES_BASE_NAME + '/' + avatar_id_name)
                instance.avatar = USER_IMAGES_BASE_NAME + '/' + avatar_id_name
                temp_shop.save()
            except (ValueError, SuspiciousFileOperation, FileNotFoundError):
                pass
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TempShopNamePutView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def put(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        temp_shop = TempShop.objects.get(unique_id=unique_id)
        serializer = BaseTempShopNamePutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(temp_shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TempShopBioPutView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def put(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        temp_shop = TempShop.objects.get(unique_id=unique_id)
        serializer = BaseTempShopBioPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(temp_shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TempShopAvailabilityPutView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def put(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        temp_shop = TempShop.objects.get(unique_id=unique_id)
        serializer = BaseTempShopAvailabilityPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(temp_shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TempShopContactPutView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def put(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        temp_shop = TempShop.objects.get(unique_id=unique_id)
        serializer = BaseTempShopContactPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(temp_shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TempShopAddressPutView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def put(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        temp_shop = TempShop.objects.get(unique_id=unique_id)
        serializer = BaseTempShopAddressPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(temp_shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TempShopColorPutView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def put(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        temp_shop = TempShop.objects.get(unique_id=unique_id)
        serializer = BaseTempShopColorPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(temp_shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TempShopFontPutView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def put(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        temp_shop = TempShop.objects.get(unique_id=unique_id)
        serializer = BaseTempShopFontPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(temp_shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
