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
from auth_shop.base.models import AuthShop, AuthShopDays
from django.core.exceptions import SuspiciousFileOperation
from auth_shop.base.tasks import base_generate_avatar_thumbnail


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
            base_generate_avatar_thumbnail.apply_async((shop.pk,), )
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get(request, *args, **kwargs):
        auth_shop_pk = kwargs.get('pk')
        try:
            shop = AuthShop.objects.get(pk=auth_shop_pk)
            shop_details_serializer = BaseGETShopInfoSerializer(shop)
            return Response(shop_details_serializer.data, status=status.HTTP_200_OK)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopAvatarPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('pk')
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
            base_generate_avatar_thumbnail.apply_async((new_avatar.pk,), )
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopNamePutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        auth_shop_pk = request.data.get('pk')
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
        auth_shop_pk = request.data.get('pk')
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
        auth_shop_pk = request.data.get('pk')
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
        auth_shop_pk = request.data.get('pk')
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
        auth_shop_pk = request.data.get('pk')
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
        auth_shop_pk = request.data.get('pk')
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
        auth_shop_pk = request.data.get('pk')
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
        auth_shop_pk = request.data.get('pk')
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
        auth_shop_pk = request.data.get('pk')
        shop = AuthShop.objects.get(pk=auth_shop_pk)
        serializer = BaseShopFontPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(shop, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
