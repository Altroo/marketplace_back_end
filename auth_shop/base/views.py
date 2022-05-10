from os import remove
from urllib.parse import quote_plus
from uuid import uuid4
from celery import current_app
from django.core.exceptions import SuspiciousFileOperation
from django.db import IntegrityError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from auth_shop.base.models import AuthShop, AuthShopDays, AskForCreatorLabel, ModeVacance
from auth_shop.base.serializers import BaseShopSerializer, BaseShopAvatarPutSerializer, \
    BaseShopNamePutSerializer, BaseShopBioPutSerializer, BaseShopAvailabilityPutSerializer, \
    BaseShopContactPutSerializer, BaseShopAddressPutSerializer, BaseShopColorPutSerializer, \
    BaseShopFontPutSerializer, BaseGETShopInfoSerializer, BaseShopTelPutSerializer, \
    BaseShopWtspPutSerializer, BaseShopAskForCreatorLabelSerializer, \
    BaseShopModeVacanceSerializer, BaseShopModeVacancePUTSerializer
from auth_shop.base.tasks import base_generate_avatar_thumbnail
from offer.base.models import Offers, Products, Services, Solder, Delivery
from temp_offer.base.models import TempOffers, TempSolder, TempDelivery
from temp_shop.base.models import TempShop
from os import path
from datetime import datetime
# import qrcode
from PIL import Image  # , ImageDraw, ImageFont
# import qrcode.image.svg
from cv2 import imread, resize, INTER_AREA, cvtColor, COLOR_BGR2RGB
from io import BytesIO
# import textwrap


class ShopView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

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
            'creator': False,
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
                'font_name': shop.font_name,
                'creator': False,
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


class ShopAvatarPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
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
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopNamePutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopNamePutSerializer(data=request.data)
            if serializer.is_valid():
                serializer.update(shop, serializer.validated_data)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopBioPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopBioPutSerializer(data=request.data)
            if serializer.is_valid():
                serializer.update(shop, serializer.validated_data)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopAvailabilityPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
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
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopContactPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopContactPutSerializer(data=request.data)
            if serializer.is_valid():
                serializer.update(shop, serializer.validated_data)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopTelPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopTelPutSerializer(data=request.data)
            if serializer.is_valid():
                serializer.update(shop, serializer.validated_data)
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopWtspPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopWtspPutSerializer(data=request.data)
            if serializer.is_valid():
                serializer.update(shop, serializer.validated_data)
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopAddressPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopAddressPutSerializer(data=request.data)
            if serializer.is_valid():
                serializer.update(shop, serializer.validated_data)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopColorPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopColorPutSerializer(data=request.data)
            if serializer.is_valid():
                serializer.update(shop, serializer.validated_data)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopFontPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopFontPutSerializer(data=request.data)
            if serializer.is_valid():
                serializer.update(shop, serializer.validated_data)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class TempShopToAuthShopView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    # @staticmethod
    # def from_img_to_io(image, format_):
    #     bytes_io = BytesIO()
    #     image.save(bytes_io, format=format_)
    #     bytes_io.seek(0)
    #     return bytes_io

    @staticmethod
    def post(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        user = request.user
        try:
            temp_shop = TempShop.objects.get(unique_id=unique_id)
            # transfer temp shop data
            try:
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
                    qaryb_link=temp_shop.qaryb_link,
                )
                auth_shop.save()
                # revoke 24h periodic task
                task_id = temp_shop.task_id
                current_app.control.revoke(task_id, terminate=True, signal='SIGKILL')
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
                        picture_1_thumbnail=temp_offer.picture_1_thumbnail,
                        picture_2_thumbnail=temp_offer.picture_2_thumbnail,
                        picture_3_thumbnail=temp_offer.picture_3_thumbnail,
                        description=temp_offer.description,
                        # For whom
                        # Tags
                        price=temp_offer.price,
                    )
                    offer.save()
                    temp_categories = temp_offer.offer_categories.all()
                    for temp_categorie in temp_categories:
                        offer.offer_categories.add(temp_categorie.pk)
                    for_whoms = temp_offer.for_whom.all()
                    for for_whom in for_whoms:
                        offer.for_whom.add(for_whom.pk)
                    tags = temp_offer.tags.all()
                    for tag in tags:
                        offer.tags.add(tag.pk)
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
                    temp_deliveries = TempDelivery.objects.filter(temp_offer=temp_offer.pk)
                    for temp_delivery in temp_deliveries:
                        delivery = Delivery.objects.create(
                            offer=offer.pk,
                            # delivery_city
                            delivery_price=temp_delivery.temp_delivery_price,
                            delivery_days=temp_delivery.temp_delivery_days,
                        )
                        delivery.save()
                        temp_delivery_cities = temp_delivery.temp_delivery_city.all()
                        for temp_delivery_city in temp_delivery_cities:
                            delivery.delivery_city.add(temp_delivery_city.pk)
                # qr_code = make(str(temp_shop.qaryb_link))
                # qr_code_img = self.from_img_to_io(qr_code, 'PNG')
                # auth_shop.save_image('qr_code_img', qr_code_img)
                temp_shop.delete()
                data = {
                    'response': 'Temp shop data transfered into Auth shop!'
                }
                return Response(data=data, status=status.HTTP_200_OK)
            except IntegrityError:
                data = {'errors': ['User already has a shop.']}
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except TempShop.DoesNotExist:
            data = {'errors': ['User temp shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopAskBecomeCreator(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            try:
                ask_for_creator = AskForCreatorLabel.objects.get(auth_shop=auth_shop)
                ask_for_creator.asked_counter = ask_for_creator.asked_counter + 1
                ask_for_creator.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except AskForCreatorLabel.DoesNotExist:
                serializer = BaseShopAskForCreatorLabelSerializer(data={
                    'auth_shop': auth_shop.pk,
                })
                if serializer.is_valid():
                    serializer.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopQrCodeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def load_image(img_path):
        loaded_img = cvtColor(imread(img_path), COLOR_BGR2RGB)
        return loaded_img

    @staticmethod
    def image_resize(image, width=None, height=None, inter=INTER_AREA):
        (h, w) = image.shape[:2]

        if width is None and height is None:
            return image

        if width is None:
            r = height / float(h)
            dim = (int(w * r), height)

        else:
            r = width / float(w)
            dim = (width, int(h * r))

        resized = resize(image, dim, interpolation=inter)
        return resized

    @staticmethod
    def from_img_to_io(image, format_):
        image = Image.fromarray(image)
        bytes_io = BytesIO()
        image.save(bytes_io, format=format_)
        bytes_io.seek(0)
        return bytes_io

    # def post(self, request, *args, **kwargs):
    #     user = request.user
    #     # TODO
    #     # from user access shop to get qaryb store link
    #     # Get color code
    #     # Get text
    #     img_path = '/Users/youness/Desktop/Qaryb_API_new/static/icons/qaryb_icon_300_300.png'
    #     loaded_img = self.load_image(img_path)
    #     resized_img = self.image_resize(loaded_img, width=1000, height=1000)
    #     img_thumbnail = self.from_img_to_io(resized_img, 'PNG')
    #     logo = Image.open(img_thumbnail)
    #     basewidth = 100
    #     wpercent = (basewidth / float(logo.size[0]))
    #     hsize = int((float(logo.size[1]) * float(wpercent)))
    #     logo = logo.resize((basewidth, hsize), Image.Resampling.LANCZOS)
    #     qr_code = qrcode.QRCode(
    #         version=1,
    #         error_correction=qrcode.constants.ERROR_CORRECT_H,
    #         box_size=10,
    #         border=10,
    #     )
    #     # taking url or text
    #     url = 'https://www.qaryb.com'
    #     # adding URL or text to QRcode
    #     qr_code.add_data(url)
    #     # generating QR code
    #     qr_code.make(fit=True)
    #     # taking color name from user
    #     qr_color = 'Black'
    #     # adding color to QR code
    #     qr_img = qr_code.make_image(fill_color=qr_color, back_color="white").convert('RGBA')
    #     # set size of QR code
    #     pos = ((qr_img.size[0] - logo.size[0]) // 2,
    #            (qr_img.size[1] - logo.size[1]) // 2)
    #     qr_img.paste(logo, pos)
    #     colors = random_color_picker()
    #     shuffle(colors)
    #     color = colors.pop()
    #     max_w, max_h = 300, 50
    #     color_box = Image.new("RGB", (max_w, max_h), color='white')
    #     # check the length of the text
    #     # if more than some characters
    #     # fit the drawn_text_img pixels
    #     drawn_text_img = ImageDraw.Draw(color_box)
    #     drawn_text_img.rounded_rectangle(((0, 0), (max_w, max_h)), 20, fill=color)
    #     # Wrap the text if it's long
    #     # Limit 40 chars
    #     astr = "123456 ABCDEF ABCDEF ABCDEF ABCDEF ABCDE"
    #     para = textwrap.wrap(astr, width=20)
    #     para = '\n'.join(para)
    #     font = ImageFont.truetype("/Users/youness/Desktop/test_qr_code/fonts/Poppins-Bold.ttf", 16)
    #     # draw the wraped text box with the font
    #     text_width, text_height = drawn_text_img.textsize(para, font=font)
    #     current_h = 3
    #     drawn_text_img.text(((max_w - text_width) / 2, current_h), para, font=font,
    #                         fill=(255, 255, 255), align='center')
    #     qr_img.paste(drawn_text_img._image, (100, 420))
    #     # qr_img.save('gfg_QR.png')
    #     # qr_img.show()
    #     # Translate img to IO
    #     qr_code_img = self.from_img_to_io(qr_code, 'PNG')
    #     # Save the QR image
    #     auth_shop.save_image('qr_code_img', qr_code_img)
    #     # Return the absolute path
    #     # qr_code_img = AuthShop.objects.get(user=user).get_absolute_qr_code_img
    #     data = {
    #         'qr_code': qr_code_img
    #     }
    #     return Response(data=data, status=status.HTTP_200_OK)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        try:
            qr_code_img = AuthShop.objects.get(user=user).get_absolute_qr_code_img
            data = {
                'qr_code': qr_code_img
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopVisitCardView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            data = {
                'avatar': auth_shop.avatar,
                'shop_name': auth_shop.shop_name,
                'user_first_name': auth_shop.user.first_name,
                'user_last_name': auth_shop.user.last_name,
                'shop_link': auth_shop.qaryb_link,
                'phone': auth_shop.phone,
                'contact_email': auth_shop.contact_email,
                'facebook_link': auth_shop.facebook_link,
                'instagram_link': auth_shop.instagram_link,
                'whatsapp': auth_shop.whatsapp,
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopModeVacanceView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.select_related('auth_shop_mode_vacance').get(user=user)
            try:
                mode_vacance_serializer = BaseShopModeVacanceSerializer(auth_shop.auth_shop_mode_vacance)
                return Response(data=mode_vacance_serializer.data, status=status.HTTP_200_OK)
            except ModeVacance.DoesNotExist:
                data = {'errors': ['Auth shop has no mode vacance.']}
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            date_from = datetime.strptime(request.data.get('date_from'), '%Y-%m-%d')
            date_to = datetime.strptime(request.data.get('date_to'), '%Y-%m-%d')
            if date_from > date_to:
                data = {'errors': ['Date from is > than date to.']}
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer = BaseShopModeVacanceSerializer(data={
                    'auth_shop': auth_shop.pk,
                    'date_from': request.data.get('date_from'),
                    'date_to': request.data.get('date_to'),
                })
                if serializer.is_valid():
                    serializer.save()
                    return Response(data=serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.select_related('auth_shop_mode_vacance').get(user=user)
            auth_shop.auth_shop_mode_vacance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found']}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.select_related('auth_shop_mode_vacance').get(user=user)
            date_from = datetime.strptime(request.data.get('date_from'), '%Y-%m-%d')
            date_to = datetime.strptime(request.data.get('date_to'), '%Y-%m-%d')
            if date_from > date_to:
                data = {'errors': ['Date from is > than date to.']}
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer = BaseShopModeVacancePUTSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.update(auth_shop.auth_shop_mode_vacance, serializer.validated_data)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
