from os import remove
from celery import current_app
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from shop.base.utils import unique_slugify
from shop.base.serializers import BaseShopSerializer, \
    BaseShopNamePutSerializer, BaseShopBioPutSerializer, BaseShopAvailabilityPutSerializer, \
    BaseShopContactPutSerializer, BaseShopAddressPutSerializer, BaseShopColorPutSerializer, \
    BaseShopFontPutSerializer, BaseGETShopInfoSerializer, BaseShopPhoneContactPutSerializer, \
    BaseShopAskForCreatorLabelSerializer, \
    BaseShopModeVacanceSerializer, BaseShopModeVacancePUTSerializer
from shop.models import AuthShop, AuthShopDays, AskForCreatorLabel, PhoneCodes
from os import path
from datetime import datetime, date
import qrcode
from PIL import Image, ImageDraw, ImageFont
import qrcode.image.svg
from io import BytesIO
from shop.base.utils import ImageProcessor
import textwrap
import arabic_reshaper
from bidi.algorithm import get_display
from shop.base.tasks import base_delete_mode_vacance_obj, base_resize_avatar_thumbnail


class ShopView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        shop_name = request.data.get('shop_name')
        color_code = request.data.get('color_code')
        bg_color_code = request.data.get('bg_color_code')
        border = request.data.get('border')
        icon_color = request.data.get('icon_color')
        font_name = request.data.get('font_name')
        serializer = BaseShopSerializer(data={
            'user': user.pk,
            'shop_name': shop_name,
            'color_code': color_code,
            'bg_color_code': bg_color_code,
            'border': border,
            'icon_color': icon_color,
            'font_name': font_name,
            'creator': False,
        })
        if serializer.is_valid():
            shop = serializer.save()
            qaryb_link = unique_slugify(instance=shop, value=shop.shop_name, slug_field_name='qaryb_link')
            shop.qaryb_link = qaryb_link
            shop.save()
            # Generate new avatar thumbnail
            avatar = request.data.get('avatar')
            # Generate new avatar thumbnail
            image_processor = ImageProcessor()
            avatar_file: ContentFile | None = image_processor.data_url_to_uploaded_file(avatar)
            base_resize_avatar_thumbnail.apply_async((
                shop.pk,
                'AuthShop',
                avatar_file.file if isinstance(avatar_file, ContentFile) else None
            ), )
            data = {
                'pk': shop.pk,
                'shop_name': shop.shop_name,
                'avatar': shop.get_absolute_avatar_img,
                'color_code': shop.color_code,
                'bg_color_code': shop.bg_color_code,
                'border': shop.border,
                'icon_color': shop.icon_color,
                'font_name': shop.font_name,
                'creator': False,
                'qaryb_link': qaryb_link
            }
            return Response(data=data, status=status.HTTP_200_OK)
        raise ValidationError(serializer.errors)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        shop_link = kwargs.get('shop_link')
        try:
            if shop_link:
                auth_shop = AuthShop.objects.get(qaryb_link=shop_link)
            else:
                auth_shop = AuthShop.objects.get(user=user)
            shop_details_serializer = BaseGETShopInfoSerializer(auth_shop)
            return Response(shop_details_serializer.data, status=status.HTTP_200_OK)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopAvatarPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            # serializer = BaseShopAvatarPutSerializer(shop, data=request.data, partial=True)
            # if serializer.is_valid():
            avatar = request.data.get('avatar')
            image_processor = ImageProcessor()
            avatar_file: ContentFile | None = image_processor.data_url_to_uploaded_file(avatar)
            if isinstance(avatar_file, ContentFile):
                if shop.avatar:
                    try:
                        remove(shop.avatar.path)
                        shop.avatar = None
                        shop.save(update_fields=['avatar'])
                    except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                        pass
                if shop.avatar_thumbnail:
                    try:
                        remove(shop.avatar_thumbnail.path)
                        shop.avatar_thumbnail = None
                        shop.save(update_fields=['avatar_thumbnail'])
                    except (ValueError, SuspiciousFileOperation, FileNotFoundError):
                        pass
                # Generate new avatar thumbnail
                base_resize_avatar_thumbnail.apply_async((
                    shop.pk,
                    'AuthShop',
                    avatar_file.file if isinstance(avatar_file, ContentFile) else None
                ), )

                data = {
                    'avatar': shop.get_absolute_avatar_img,
                }
                return Response(data=data, status=status.HTTP_200_OK)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopNamePutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopNamePutSerializer(shop, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            raise ValidationError(serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopBioPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopBioPutSerializer(shop, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            raise ValidationError(serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopAvailabilityPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        morning_hour_from = request.data.get('morning_hour_from', '')
        morning_hour_to = request.data.get('morning_hour_to', '')
        afternoon_hour_from = request.data.get('afternoon_hour_from', '')
        afternoon_hour_to = request.data.get('afternoon_hour_to', '')
        opening_days = str(request.data.get('opening_days')).split(',')
        opening_days = AuthShopDays.objects.filter(code_day__in=opening_days)
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopAvailabilityPutSerializer(shop, data={
                'morning_hour_from': morning_hour_from,
                'morning_hour_to': morning_hour_to,
                'afternoon_hour_from': afternoon_hour_from,
                'afternoon_hour_to': afternoon_hour_to,
            }, partial=True)
            if serializer.is_valid():
                new_availability = serializer.save()
                new_availability.opening_days.clear()
                days_list = []
                for day in opening_days:
                    new_availability.opening_days.add(day.pk)
                    days_list.append({
                        'pk': day.pk,
                        'code_day': day.code_day,
                        'name_day': day.name_day
                    })
                data = {
                    'opening_days': days_list,
                    'morning_hour_from': serializer.data.get('morning_hour_from'),
                    'morning_hour_to': serializer.data.get('morning_hour_to'),
                    'afternoon_hour_from': serializer.data.get('afternoon_hour_from'),
                    'afternoon_hour_to': serializer.data.get('afternoon_hour_to'),
                }
                return Response(data=data, status=status.HTTP_200_OK)
            raise ValidationError(serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopContactPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopContactPutSerializer(shop, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            raise ValidationError(serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopPhoneContactPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopPhoneContactPutSerializer(shop, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            raise ValidationError(serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopAddressPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopAddressPutSerializer(shop, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            raise ValidationError(serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopColorPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopColorPutSerializer(shop, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            raise ValidationError(serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopFontPutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            serializer = BaseShopFontPutSerializer(shop, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            raise ValidationError(serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


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
                raise ValidationError(serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopQrCodeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def from_img_to_io(image, format_, type_):
        if type_ == 'input':
            image = Image.fromarray(image)
        # type == 'output'
        bytes_io = BytesIO()
        image.save(bytes_io, format=format_)
        bytes_io.seek(0)
        return bytes_io

    @staticmethod
    def get_text_fill_color(bg_color):
        # white 255, 255, 255
        # black 0, 0, 0
        match bg_color:
            case ("#F3DCDC" | "#FFD9A2" | "#F8F2DA" | "#DBF4EA" | "#DBE8F4" | "#D5CEEE" | "#F3D8E1" | "#EBD2AD"
                  | "#E2E4E2" | "#FFFFFF" | "#FFA826" | "#FED301" | "#07CBAD" | "#FF9DBF" | "#CEB186"):
                return 0, 0, 0
            case ("#FF5D6B" | "#0274D7" | "#8669FB" | "#878E88" | "#0D070B"):
                return 255, 255, 255
            case _:
                # Return black color as default
                return 0, 0, 0

    def post(self, request, *args, **kwargs):
        user = request.user
        bg_color = request.data.get('bg_color')
        qr_text = request.data.get('qr_text')
        if len(str(qr_text)) > 60:
            errors = {"qr_text": ["Qr code text should be less than 60 characters."]}
            raise ValidationError(errors)
        try:
            auth_shop = AuthShop.objects.get(user=user)
            qaryb_link = auth_shop.qaryb_link
            icon_path = self.parent_file_dir + '/static/icons/qaryb_icon_300_300.png'
            image_processor = ImageProcessor()
            loaded_img = image_processor.load_image(icon_path)
            resized_img = image_processor.image_resize(loaded_img, width=1000, height=1000)
            img_thumbnail = self.from_img_to_io(resized_img, 'WEBP', 'input')
            logo = Image.open(img_thumbnail)
            basewidth = 100
            wpercent = (basewidth / float(logo.size[0]))
            hsize = int((float(logo.size[1]) * float(wpercent)))
            logo = logo.resize((basewidth, hsize), Image.Resampling.LANCZOS)
            qr_code = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=10,
            )
            qr_code.add_data(qaryb_link)
            qr_code.make(fit=True)
            qr_img = qr_code.make_image(fill_color='Black', back_color='white').convert('RGBA')
            pos = ((qr_img.size[0] - logo.size[0]) // 2,
                   (qr_img.size[1] - logo.size[1]) // 2)
            qr_img.paste(logo, pos)
            max_w, max_h = qr_img.size[0] - qr_code.box_size ** 2 - qr_code.border ** 2, 60
            color_box = Image.new("RGB", (max_w, max_h), color='white')
            drawn_text_img = ImageDraw.Draw(color_box)
            drawn_text_img.rounded_rectangle(((0, 0), (max_w, max_h)), 20, fill=bg_color)
            unicode_text_reshaped = arabic_reshaper.reshape(qr_text)
            para = textwrap.wrap(unicode_text_reshaped, width=35)
            para = '\n'.join(para)
            unicode_text_reshaped_rtl = get_display(para, base_dir='R')
            unicode_font = ImageFont.truetype(self.parent_file_dir + '/static/fonts/Changa-Regular.ttf', 20)
            fill = self.get_text_fill_color(bg_color)
            text_width, text_height = drawn_text_img.textsize(unicode_text_reshaped_rtl, font=unicode_font)
            drawn_text_img.text(((max_w - text_width) / 2, (max_h - text_height - 10) / 2), unicode_text_reshaped_rtl,
                                align='center', font=unicode_font,
                                fill=fill)
            pos_for_text = ((qr_img.size[0] - drawn_text_img._image.width) // 2,
                            (qr_img.size[1] - drawn_text_img._image.height - 20))
            qr_img.paste(drawn_text_img._image, pos_for_text)
            qr_code_img = self.from_img_to_io(qr_img, 'WEBP', 'output')
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # Delete old qr code before generating new one
            try:
                old_qr_code_img = auth_shop.qr_code_img.path
                remove(old_qr_code_img)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            auth_shop.save_qr_code('qr_code_img', qr_code_img, uid)
            qr_code_img = AuthShop.objects.get(user=user).get_absolute_qr_code_img
            data = {
                'qr_code': qr_code_img
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except AuthShop.DoesNotExist:
            errors = {"error": ["User doesn't own a shop yet."]}
            raise ValidationError(errors)

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
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopVisitCardView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            data = {
                'avatar': auth_shop.get_absolute_avatar_thumbnail,
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
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


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
            except auth_shop.auth_shop_mode_vacance.DoesNotExist:
                return Response(data={}, status=status.HTTP_200_OK)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            date_from = datetime.strptime(request.data.get('date_from'), '%Y-%m-%d')
            date_to = datetime.strptime(request.data.get('date_to'), '%Y-%m-%d')
            if date_from > date_to:
                errors = {"error": ["Date from is > than date to."]}
                raise ValidationError(errors)
            else:
                serializer = BaseShopModeVacanceSerializer(data={
                    'auth_shop': auth_shop.pk,
                    'date_from': request.data.get('date_from'),
                    'date_to': request.data.get('date_to'),
                })
                if serializer.is_valid():
                    mode_vacance = serializer.save()
                    mode_vacance.save()
                    # Generate new periodic task
                    today_date = date.today()
                    mode_vacance_to = mode_vacance.date_to
                    days_left = mode_vacance_to - today_date
                    shift = datetime.utcnow() + days_left
                    mode_vacance_task_id = base_delete_mode_vacance_obj.apply_async((mode_vacance.pk,), eta=shift)
                    auth_shop.mode_vacance_task_id = str(mode_vacance_task_id)
                    auth_shop.save()
                    return Response(data=serializer.data, status=status.HTTP_200_OK)
                raise ValidationError(serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)

    @staticmethod
    def delete(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.select_related('auth_shop_mode_vacance').get(user=user)
            try:
                auth_shop.auth_shop_mode_vacance.delete()
                # revoke mode vacance periodic task
                mode_vacance_task_id = auth_shop.mode_vacance_task_id
                current_app.control.revoke(mode_vacance_task_id, terminate=True, signal='SIGKILL')
                auth_shop.mode_vacance_task_id = None
                auth_shop.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except auth_shop.auth_shop_mode_vacance.DoesNotExist:
                errors = {"error": ["Mode vacance not found."]}
                raise ValidationError(errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.select_related('auth_shop_mode_vacance').get(user=user)
            try:
                date_from = datetime.strptime(request.data.get('date_from'), '%Y-%m-%d')
                date_to = datetime.strptime(request.data.get('date_to'), '%Y-%m-%d')
                if date_from > date_to:
                    errors = {"error": ["Date from is > than date to."]}
                    raise ValidationError(errors)
                else:
                    serializer = BaseShopModeVacancePUTSerializer(auth_shop.auth_shop_mode_vacance,
                                                                  data=request.data, partial=True)
                    if serializer.is_valid():
                        # serializer.update(auth_shop.auth_shop_mode_vacance, serializer.validated_data)
                        serializer.save()
                        # revoke previous mode vacance periodic task
                        mode_vacance_task_id = auth_shop.mode_vacance_task_id
                        current_app.control.revoke(mode_vacance_task_id, terminate=True, signal='SIGKILL')
                        auth_shop.mode_vacance_task_id = None
                        auth_shop.save()
                        # Generate new periodic task
                        today_date = date.today()
                        mode_vacance_to = serializer.validated_data.get('date_to')
                        days_left = mode_vacance_to - today_date
                        shift = datetime.utcnow() + days_left
                        mode_vacance_task_id = base_delete_mode_vacance_obj.apply_async(
                            (serializer.validated_data.get('pk'),), eta=shift)
                        auth_shop.mode_vacance_task_id = str(mode_vacance_task_id)
                        auth_shop.save()
                        return Response(data=serializer.data, status=status.HTTP_200_OK)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except auth_shop.auth_shop_mode_vacance.DoesNotExist:
                errors = {"error": ["Mode vacance not found."]}
                raise ValidationError(errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopGetPhoneCodesView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        data = {}
        phone_codes = PhoneCodes.objects.all().order_by('phone_code').values_list('phone_code', flat=True)
        data['phone_codes'] = phone_codes
        return Response(data=data, status=status.HTTP_200_OK)
