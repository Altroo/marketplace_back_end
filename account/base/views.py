from random import choice
from string import digits
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.account.models import EmailAddress
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import logout
from django.core.exceptions import SuspiciousFileOperation
from django.template.loader import render_to_string
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from Qaryb_API_new.settings import SIMPLE_JWT
from celery import current_app
from datetime import timedelta, timezone
import datetime
from account.base.serializers import BaseRegistrationSerializer, BasePasswordResetSerializer, \
    BaseUserEmailSerializer, BaseProfilePutSerializer, BaseProfileGETSerializer, BaseBlockUserSerializer, \
    BaseBlockedUsersListSerializer, BaseReportPostsSerializer, BaseUserAddresseDetailSerializer, \
    BaseUserAddressSerializer, BaseUserAddressesListSerializer, BaseUserAddressPutSerializer, \
    BaseSocialAccountSerializer, BaseEnclosedAccountsSerializer, BaseEmailPutSerializer, \
    BaseRegistrationEmailAddressSerializer, BaseDeletedAccountsSerializer
from account.base.tasks import base_generate_user_thumbnail, base_mark_every_messages_as_read, \
    base_delete_user_media_files, base_send_email
from account.models import CustomUser, BlockedUsers, UserAddress
from os import remove
from shop.models import AuthShop
from shop.base.tasks import base_generate_avatar_thumbnail
from account.base.tasks import base_start_deleting_expired_codes
from offers.models import Offers
from places.models import City, Country
from dj_rest_auth.views import PasswordChangeView
from dj_rest_auth.views import LoginView as Dj_rest_login
from dj_rest_auth.views import LogoutView as Dj_rest_logout
from chat.models import Status, MessageModel
from dj_rest_auth.registration.views import SocialConnectView, SocialAccountListView


class FacebookLoginView(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter

    # Email Address auto added : primary true - verified true
    def login(self):
        super(FacebookLoginView, self).login()
        user = CustomUser.objects.get(pk=self.user.pk)
        user.is_enclosed = False
        user.save()
        try:
            user_status = Status.objects.get(user=self.user)
            user_status.online = True
            user_status.save()
        except Status.DoesNotExist:
            Status.objects.create(user=self.user, online=True)
        channel_layer = get_channel_layer()
        my_set = set()
        result_msg_user = MessageModel.objects.filter(user=self.user.pk)
        result_msg_recipient = MessageModel.objects.filter(recipient=self.user.pk)
        for i in result_msg_user:
            if i != self.user.pk:
                my_set.add(i.recipient.pk)
        for i in result_msg_recipient:
            if i != self.user.pk:
                my_set.add(i.user.pk)
        for user_pk in CustomUser.objects.filter(id__in=my_set, status__online=True) \
                .exclude(is_active=False).values_list('id', flat=True):
            if Status.objects.filter(user__id=user_pk).exists() and Status.objects.get(
                    user__id=user_pk).online:
                event = {
                    "type": "recieve_group_message",
                    "message": {
                        "type": "USER_STATUS",
                        "user": self.user.pk,
                        "online": True,
                        "recipient": user_pk,
                    }
                }
                async_to_sync(channel_layer.group_send)("%s" % user_pk, event)


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

    # Email Address auto added : primary true - verified true
    def login(self):
        super(GoogleLoginView, self).login()
        user = CustomUser.objects.get(pk=self.user.pk)
        user.is_enclosed = False
        user.save()
        try:
            user_status = Status.objects.get(user=self.user)
            user_status.online = True
            user_status.save()
        except Status.DoesNotExist:
            Status.objects.create(user=self.user, online=True)
        channel_layer = get_channel_layer()
        my_set = set()
        result_msg_user = MessageModel.objects.filter(user=self.user.pk)
        result_msg_recipient = MessageModel.objects.filter(recipient=self.user.pk)
        for i in result_msg_user:
            if i != self.user.pk:
                my_set.add(i.recipient.pk)
        for i in result_msg_recipient:
            if i != self.user.pk:
                my_set.add(i.user.pk)
        for user_pk in CustomUser.objects.filter(id__in=my_set, status__online=True) \
                .exclude(is_active=False).values_list('id', flat=True):
            if Status.objects.filter(user__id=user_pk).exists() and Status.objects.get(
                    user__id=user_pk).online:
                event = {
                    "type": "recieve_group_message",
                    "message": {
                        "type": "USER_STATUS",
                        "user": self.user.pk,
                        "online": True,
                        "recipient": user_pk,
                    }
                }
                async_to_sync(channel_layer.group_send)("%s" % user_pk, event)


class FacebookLinkingView(SocialConnectView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLinkingView(SocialConnectView):
    adapter_class = GoogleOAuth2Adapter


class GetSocialAccountListView(SocialAccountListView):
    serializer_class = BaseSocialAccountSerializer
    pagination_class = None


class ChangePasswordView(PasswordChangeView):

    def post(self, request, *args, **kwargs):
        super(ChangePasswordView, self).post(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegistrationView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def generate_random_code(length=4):
        return ''.join(choice(digits) for _ in range(length))

    def post(self, request):
        password = request.data.get('password')
        password2 = request.data.get('password2')
        email = str(request.data.get('email')).lower()
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        serializer = BaseRegistrationSerializer(data={
            'email': email,
            'password': password,
            'password2': password2,
            'first_name': first_name,
            'last_name': last_name
        })
        if serializer.is_valid():
            user = serializer.save()
            email_address_serializer = BaseRegistrationEmailAddressSerializer(data={
                'user': user.pk,
                'email': email,
                'primary': True
            })
            if email_address_serializer.is_valid():
                email_address_serializer.save()
                mail_subject = 'Vérifiez votre compte'
                mail_template = 'activate_account.html'
                code = self.generate_random_code()
                message = render_to_string(mail_template, {
                    'first_name': user.first_name,
                    'code': code
                })
                base_send_email.apply_async((user.pk, email, mail_subject, message, code, 'activation_code'), )
                # Generate refresh token
                refresh = RefreshToken.for_user(user)
                date_now = datetime.datetime.now(timezone.utc)
                data = {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "user": {
                        "pk": user.pk,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    },
                    "access_token_expiration": (date_now + SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']),
                    "refresh_token_expiration": (date_now + SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'])
                }
                # Generate user avatar and thumbnail
                base_generate_user_thumbnail.apply_async((user.pk,), )
                shift = date_now + timedelta(hours=24)
                task_id_activation = base_start_deleting_expired_codes.apply_async((user.pk, 'activation'), eta=shift)
                user.task_id_activation = str(task_id_activation)
                user.save()
                return Response(data=data, status=status.HTTP_200_OK)
            return Response(email_address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        raise ValidationError(serializer.errors)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyAccountView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        email = str(request.data.get('email')).lower()
        code = request.data.get('code')
        try:
            user = CustomUser.objects.get(email=email)
            user_email = EmailAddress.objects.get(email=email)
            if user_email.verified:
                return Response(status=status.HTTP_204_NO_CONTENT)
            if code is not None and email is not None:
                # revoke 24h previous periodic task (default activation)
                task_id_activation = user.task_id_activation
                if task_id_activation:
                    current_app.control.revoke(task_id_activation, terminate=True, signal='SIGKILL')
                    user.task_id_activation = None
                    user.activation_code = ''
                    user.save()
                user_email.verified = True
                user_email.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            data = {
                'errors': "User or Verification code invalid!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            data = {
                'errors': "User or Verification code invalid!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationCodeView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def generate_random_code(length=4):
        return ''.join(choice(digits) for _ in range(length))

    def post(self, request, *args, **kwargs):
        email = str(request.data.get('email')).lower()
        try:
            user = CustomUser.objects.get(email=email)
            # revoke 24h previous periodic task (default activation)
            task_id_activation = user.task_id_activation
            if task_id_activation:
                current_app.control.revoke(task_id_activation, terminate=True, signal='SIGKILL')
                user.task_id_activation = None
                user.save()
            mail_subject = 'Vérifiez votre compte'
            mail_template = 'activate_account.html'
            # if user.activation_code:
            #    code = user.activation_code
            # else:
            code = self.generate_random_code()
            message = render_to_string(mail_template, {
                'first_name': user.first_name,
                'code': code,
            })
            base_send_email.apply_async((user.pk, email, mail_subject, message, code, 'activation_code'), )
            date_now = datetime.datetime.now(timezone.utc)
            shift = date_now + timedelta(hours=24)
            task_id_activation = base_start_deleting_expired_codes.apply_async((user.pk, 'activation'), eta=shift)
            user.task_id_activation = str(task_id_activation)
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            data = {
                'email': "User Doesn't exist!"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class SendPasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def generate_random_code(length=4):
        return ''.join(choice(digits) for _ in range(length))

    def post(self, request):
        email = str(request.data.get('email')).lower()
        try:
            user = CustomUser.objects.get(email=email)
            if user.email is not None:
                serializer = BaseUserEmailSerializer(data=request.data)
                if serializer.is_valid():
                    # revoke 24h previous periodic task (default password_reset)
                    task_id_password_reset = user.task_id_password_reset
                    if task_id_password_reset:
                        current_app.control.revoke(task_id_password_reset, terminate=True, signal='SIGKILL')
                        user.task_id_password_reset = None
                        user.save()
                    mail_subject = 'Renouvellement du mot de passe'
                    mail_template = 'password_reset.html'
                    code = self.generate_random_code()
                    message = render_to_string(mail_template, {
                        'first_name': user.first_name,
                        'code': code,
                    })
                    base_send_email.apply_async((user.pk, user.email, mail_subject, message, code,
                                                 'password_reset_code'), )
                    date_now = datetime.datetime.now(timezone.utc)
                    shift = date_now + timedelta(hours=24)
                    task_id_password_reset = base_start_deleting_expired_codes.apply_async((user.pk, 'password_reset'),
                                                                                           eta=shift)
                    user.task_id_password_reset = str(task_id_password_reset)
                    user.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            data = {
                'email': "User Doesn't exist!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        email = str(kwargs.get('email')).lower()
        code = kwargs.get('code')
        try:
            user = CustomUser.objects.get(email=email)
            if code is not None and code == user.password_reset_code:
                return Response(status=status.HTTP_204_NO_CONTENT)
            data = {
                'errors': "User or Verification code invalid!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            data = {
                'errors': "User or Verification code invalid!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(request, *args, **kwargs):
        email = str(request.data.get('email')).lower()
        code = request.data.get('code')
        try:
            user = CustomUser.objects.get(email=email)
            if code is not None and email is not None and code == user.password_reset_code:
                serializer = BasePasswordResetSerializer(data=request.data)
                if serializer.is_valid():
                    # revoke 24h previous periodic task (default password_reset)
                    if user.task_id_password_reset:
                        task_id_password_reset = user.task_id_password_reset
                        current_app.control.revoke(task_id_password_reset, terminate=True, signal='SIGKILL')
                        user.task_id_password_reset = None
                        user.save()
                    # Check old password
                    new_password = serializer.data.get("new_password")
                    new_password2 = serializer.data.get("new_password2")
                    # set_password also hashes the password that the user will get
                    if new_password != new_password2:
                        return Response({"new_password": ["Passwords doesn't match!"]},
                                        status=status.HTTP_400_BAD_REQUEST)
                    user.set_password(serializer.data.get("new_password"))
                    user.password_reset_code = ''
                    user.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            data = {
                'errors': "User or Verification code invalid!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            data = {
                'errors': "User or Verification code invalid!"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class CheckEmailView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        email = str(request.data.get('email')).lower()
        try:
            CustomUser.objects.get(email=email)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(Dj_rest_login):
    def login(self):
        super(LoginView, self).login()
        user = CustomUser.objects.get(pk=self.user.pk)
        user.is_enclosed = False
        user.save()
        try:
            user_status = Status.objects.get(user=self.user)
            user_status.online = True
            user_status.save()
        except Status.DoesNotExist:
            Status.objects.create(user=self.user, online=True)
        channel_layer = get_channel_layer()
        my_set = set()
        result_msg_user = MessageModel.objects.filter(user=self.user.pk)
        result_msg_recipient = MessageModel.objects.filter(recipient=self.user.pk)
        for i in result_msg_user:
            if i != self.user.pk:
                my_set.add(i.recipient.pk)
        for i in result_msg_recipient:
            if i != self.user.pk:
                my_set.add(i.user.pk)
        for user_pk in CustomUser.objects.filter(id__in=my_set, status__online=True) \
                .exclude(is_active=False).values_list('id', flat=True):
            if Status.objects.filter(user__id=user_pk).exists() and Status.objects.get(
                    user__id=user_pk).online:
                event = {
                    "type": "recieve_group_message",
                    "message": {
                        "type": "USER_STATUS",
                        "user": self.user.pk,
                        "online": True,
                        "recipient": user_pk,
                    }
                }
                async_to_sync(channel_layer.group_send)("%s" % user_pk, event)


class LogoutView(Dj_rest_logout):
    permission_classes = (permissions.IsAuthenticated,)

    def logout(self, request):
        try:
            user_status = Status.objects.get(user=request.user)
            user_status.online = False
            user_status.save()
        except Status.DoesNotExist:
            Status.objects.create(user=request.user, online=False)
        channel_layer = get_channel_layer()
        my_set = set()
        result_msg_user = MessageModel.objects.filter(user=request.user.pk)
        result_msg_recipient = MessageModel.objects.filter(recipient=request.user.pk)
        for i in result_msg_user:
            if i != request.user.pk:
                my_set.add(i.recipient.pk)
        for i in result_msg_recipient:
            if i != request.user.pk:
                my_set.add(i.user.pk)
        for user_id in CustomUser.objects.filter(id__in=my_set, status__online=True) \
                .exclude(is_active=False).values_list('id', flat=True):
            if Status.objects.filter(user__id=user_id).exists() and Status.objects.get(user__id=user_id).online:
                event = {
                    "type": "recieve_group_message",
                    "message": {
                        "type": "USER_STATUS",
                        "user": request.user.pk,
                        "online": False,
                        "recipient": user_id,
                    }
                }
                async_to_sync(channel_layer.group_send)("%s" % user_id, event)
        return super(LogoutView, self).logout(request)


class GetProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user_pk = kwargs.get('user_pk')
        # TODO missing shop name, offer categories, offer products, ratings (buys, sells)
        try:
            user = CustomUser.objects.get(pk=user_pk)
            user_serializer = BaseProfileGETSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            data = {'errors': ["User Doesn't exist!"]}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        try:
            user = CustomUser.objects.get(pk=request.user.pk)
            user_serializer = BaseProfileGETSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            data = {'errors': ["User Doesn't exist!"]}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = CustomUser.objects.get(pk=request.user.pk)
        city_pk = request.data.get('city_pk')
        country_pk = request.data.get('country_pk')
        try:
            city = City.objects.get(pk=city_pk)
            country = Country.objects.get(pk=country_pk)
        except (City.DoesNotExist, Country.DoesNotExist):
            data = {'errors': ["City or Country Doesn't exist!"]}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        data = {
            'avatar': request.data.get('avatar', None),
            'first_name': request.data.get('first_name'),
            'last_name': request.data.get('last_name'),
            'gender': request.data.get('gender', ''),
            'birth_date': request.data.get('birth_date'),
            'city': city_pk,
            'country': country_pk,
        }
        serializer = BaseProfilePutSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            if user.avatar:
                try:
                    remove(user.avatar.path)
                except (ValueError, SuspiciousFileOperation, FileNotFoundError):
                    pass
            if user.avatar_thumbnail:
                try:
                    remove(user.avatar_thumbnail.path)
                except (ValueError, SuspiciousFileOperation, FileNotFoundError):
                    pass
            # new_avatar = serializer.update(user, serializer.validated_data)
            new_avatar = serializer.save()
            # Generate new avatar thumbnail
            base_generate_avatar_thumbnail.apply_async((new_avatar.pk, 'CustomUser'), )
            data['pk'] = user.pk
            data['avatar'] = user.get_absolute_avatar_img
            data['avatar_thumbnail'] = user.get_absolute_avatar_thumbnail
            data['city'] = {
                'pk': city.pk,
                'name': city.name_fr,
            }
            data['country'] = {
                'pk': country.pk,
                'name': country.name_fr,
            }
            data['date_joined'] = user.date_joined
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlockView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        blocked_users = BlockedUsers.objects.filter(user=request.user)
        serializer = BaseBlockedUsersListSerializer(blocked_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def post(request, *args, **kwargs):
        user_pk = request.user.pk
        user_blocked_pk = request.data.get('user_pk')
        if user_pk == user_blocked_pk:
            data = {'errors': ['You can\'t block yourself!']}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        serializer = BaseBlockUserSerializer(data={
            "user": user_pk,
            "user_blocked": user_blocked_pk,
        })
        if serializer.is_valid():
            serializer.save()
            base_mark_every_messages_as_read.apply_async((user_blocked_pk, user_pk), )
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        user_blocked_pk = kwargs.get('user_pk')
        try:
            BlockedUsers.objects.get(user=request.user, user_blocked=user_blocked_pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BlockedUsers.DoesNotExist:
            data = {"errors": ["User not found"]}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class ReportView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user_reported = request.data.get('user_pk')
        report_reason = request.data.get('report_reason')
        serializer = BaseReportPostsSerializer(data={
            "user": request.user.pk,
            "user_reported": user_reported,
            "report_reason": report_reason,
        })
        if serializer.is_valid():
            serializer.save()
            # TODO check if we'll get notification emails on repported users
            # check_repport_email_limit = BaseCheckRepportEmailLimit()
            # check_repport_email_limit.apply_async((post_id,), )
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user_pk = request.user
        address_pk = kwargs.get('address_pk')
        try:
            user_address = UserAddress.objects.get(user=user_pk, pk=address_pk)
            user_address_details_serializer = BaseUserAddresseDetailSerializer(user_address)
            return Response(user_address_details_serializer.data, status=status.HTTP_200_OK)
        except UserAddress.DoesNotExist:
            data = {"errors": ["Address not found."]}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def post(request, *args, **kwargs):
        user_pk = request.user.pk
        title = request.data.get('title')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        address = request.data.get('address')
        city = request.data.get('city_pk')
        zip_code = request.data.get('zip_code')
        country = request.data.get('country_pk')
        phone = request.data.get('phone')
        email = request.data.get('email')
        serializer = BaseUserAddressSerializer(data={
            "user": user_pk,
            "title": title,
            "first_name": first_name,
            "last_name": last_name,
            "address": address,
            "city": city,
            "zip_code": zip_code,
            "country": country,
            "phone": phone,
            "email": email,
        })
        if serializer.is_valid():
            serializer.save()
            data = {
                "pk": serializer.data.get('pk'),
                "title": serializer.data.get('title'),
                "first_name": serializer.data.get('first_name'),
                "last_name": serializer.data.get('last_name'),
                "address": serializer.data.get('address'),
                "zip_code": serializer.data.get('zip_code'),
                "phone": serializer.data.get('phone'),
                "email": serializer.data.get('email'),
            }
            if city is not None:
                city = City.objects.get(pk=city)
                city = {'pk': city.pk, 'name': city.name_fr},
            if country is not None:
                country = Country.objects.get(pk=country)
                country = {'pk': country.pk, 'name': country.name_fr, 'code': country.code},
            data['city'] = city
            data['country'] = country
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def patch(request, *args, **kwargs):
        user_pk = request.user
        address_pk = request.data.get('address_pk')
        user_address = UserAddress.objects.get(user=user_pk, pk=address_pk)
        data = {
            "title": request.data.get('title'),
            "first_name": request.data.get('first_name'),
            "last_name": request.data.get('last_name'),
            "address": request.data.get('address'),
            "city": request.data.get('city_pk'),
            "zip_code": request.data.get('zip_code'),
            "country": request.data.get('country_pk'),
            "phone": request.data.get('phone'),
            "email": request.data.get('email'),
        }
        serializer = BaseUserAddressPutSerializer(user_address, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        user = request.user
        address_pk = kwargs.get('address_pk')
        try:
            UserAddress.objects.get(user=user, pk=address_pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserAddress.DoesNotExist:
            data = {"errors": "Address not found."}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class GetAllAddressesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        addresses = UserAddress.objects.filter(user=user)
        serializer = BaseUserAddressesListSerializer(addresses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EncloseAccountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user_pk = request.user.pk
        reason_choice = request.data.get('reason_choice')
        typed_reason = request.data.get('typed_reason', '')
        serializer = BaseEnclosedAccountsSerializer(data={
            "user": user_pk,
            "reason_choice": reason_choice,
            "typed_reason": typed_reason,
        })
        if serializer.is_valid():
            serializer.save()
            user = CustomUser.objects.get(pk=user_pk)
            user.is_enclosed = True
            user.save()
            logout(request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class ChangeEmailAccountView(APIView):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     @staticmethod
#     def put(request, *args, **kwargs):
#         user = request.user
#         has_password = user.has_usable_password()
#         new_email = request.data.get('new_email')
#         data = {}
#         try:
#             CustomUser.objects.get(email=new_email)
#             data['email'] = ['This email address already exists.']
#             return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
#         except CustomUser.DoesNotExist:
#             # Require email & password
#             if has_password:
#                 password = request.data.get('password')
#                 if not user.check_password(password):
#                     return Response({"password": ["Sorry, but this is a wrong password."]},
#                                     status=status.HTTP_400_BAD_REQUEST)
#                 else:
#                     serializer = BaseEmailPutSerializer(data={'email': new_email})
#                     if serializer.is_valid():
#                         serializer.update(request.user, serializer.validated_data)
#                         email_address = EmailAddress.objects.get(user=user)
#                         email_address.email = new_email
#                         email_address.verified = False
#                         email_address.save()
#                         return Response(status=status.HTTP_204_NO_CONTENT)
#                     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#             else:
#                 # Require email & to set a new password
#                 new_password = request.data.get("new_password")
#                 new_password2 = request.data.get("new_password2")
#                 if new_password != new_password2:
#                     return Response({"new_password": ["Sorry, the passwords do not match."]},
#                                     status=status.HTTP_400_BAD_REQUEST)
#                 elif len(new_password) < 8 or len(new_password2) < 8:
#                     data = {'Error': {'password': ["The password must be at least 8 characters long."]}}
#                     return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
#                 serializer = BaseEmailPutSerializer(data={'email': new_email})
#                 if serializer.is_valid():
#                     serializer.update(request.user, serializer.validated_data)
#                     user.set_password(new_password)
#                     user.save()
#                     email_address = EmailAddress.objects.get(user=user)
#                     email_address.email = new_email
#                     email_address.verified = False
#                     email_address.save()
#                     return Response(status=status.HTTP_200_OK)
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeEmailHasPasswordAccountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        new_email = request.data.get('new_email')
        try:
            CustomUser.objects.get(email=new_email)
            data = {
                "email": "This email address already exists."
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            # Require email & password
            password = request.data.get('password')
            if not user.check_password(password):
                return Response({"password": ["Sorry, but this is a wrong password."]},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer = BaseEmailPutSerializer(data={'email': new_email})
                if serializer.is_valid():
                    serializer.update(request.user, serializer.validated_data)
                    email_address = EmailAddress.objects.get(user=user)
                    email_address.email = new_email
                    email_address.verified = False
                    email_address.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeEmailNotHasPasswordAccountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = request.user
        new_email = request.data.get('new_email')
        try:
            CustomUser.objects.get(email=new_email)
            data = {
                "email": "This email address already exists."
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            # Require email & to set a new password
            new_password = request.data.get("new_password")
            new_password2 = request.data.get("new_password2")
            if new_password != new_password2:
                return Response({"new_password": ["Sorry, the passwords do not match."]},
                                status=status.HTTP_400_BAD_REQUEST)
            elif len(new_password) < 8 or len(new_password2) < 8:
                data = {'Error': {'password': ["The password must be at least 8 characters long."]}}
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
            serializer = BaseEmailPutSerializer(data={'email': new_email})
            if serializer.is_valid():
                serializer.update(request.user, serializer.validated_data)
                user.set_password(new_password)
                user.save()
                email_address = EmailAddress.objects.get(user=user)
                email_address.email = new_email
                email_address.verified = False
                email_address.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckAccountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        has_password = user.has_usable_password()
        try:
            check_verified = EmailAddress.objects.get(user=user).verified
            try:
                AuthShop.objects.get(user=user)
                has_shop = True
            except AuthShop.DoesNotExist:
                has_shop = False
            data = {
                "email": user.email,
                "verified": check_verified,
                "has_password": has_password,
                "has_shop": has_shop,
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except EmailAddress.DoesNotExist:
            data = {
                "email": "Email not found."
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class DeleteAccountView(APIView):

    @staticmethod
    def delete(request, *args, **kwargs):
        user = request.user
        reason_choice = request.data.get('reason_choice')
        typed_reason = request.data.get('typed_reason')
        serializer = BaseDeletedAccountsSerializer(data={
            "email": user.email,
            "reason_choice": reason_choice,
            "typed_reason": typed_reason,
        })
        if serializer.is_valid():
            serializer.save()
            media_paths_list = []
            # Delete user avatars
            if user.avatar:
                media_paths_list.append(user.avatar.path)
            if user.avatar_thumbnail:
                media_paths_list.append(user.avatar_thumbnail.path)
            # Media chat
            chat_msgs_sent = MessageModel.objects.filter(user__pk=user.pk)
            for msg_sent in chat_msgs_sent:
                if msg_sent.attachment:
                    media_paths_list.append(msg_sent.attachment.path)
                if msg_sent.attachment_thumbnail:
                    media_paths_list.append(msg_sent.attachment_thumbnail.path)
            chat_msgs_received = MessageModel.objects.filter(recipient__pk=user.pk)
            for msg_received in chat_msgs_received:
                if msg_received.attachment:
                    media_paths_list.append(msg_received.attachment.path)
                if msg_received.attachment_thumbnail:
                    media_paths_list.append(msg_received.attachment_thumbnail.path)
            try:
                auth_shop = AuthShop.objects.get(user__pk=user.pk)
                # Media Shop avatars
                if auth_shop.avatar:
                    media_paths_list.append(auth_shop.avatar.path)
                if auth_shop.avatar_thumbnail:
                    media_paths_list.append(auth_shop.avatar_thumbnail.path)
                # Media Shop qrcodes
                if auth_shop.qr_code_img:
                    media_paths_list.append(auth_shop.qr_code_img.path)
                # Media Shop offers
                offers = Offers.objects.filter(auth_shop=auth_shop)
                for offer in offers:
                    if offer.picture_1:
                        media_paths_list.append(offer.picture_1.path)
                    if offer.picture_1_thumbnail:
                        media_paths_list.append(offer.picture_1_thumbnail.path)
                    if offer.picture_2:
                        media_paths_list.append(offer.picture_2.path)
                    if offer.picture_2_thumbnail:
                        media_paths_list.append(offer.picture_2_thumbnail.path)
                    if offer.picture_3:
                        media_paths_list.append(offer.picture_3.path)
                    if offer.picture_3_thumbnail:
                        media_paths_list.append(offer.picture_3_thumbnail.path)
                auth_shop.delete()
            except AuthShop.DoesNotExist:
                pass
            # delete here
            base_delete_user_media_files.apply_async((media_paths_list,), )
            # base_delete_user_account.apply_async((user.pk,), )
            user.delete()
            logout(request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
