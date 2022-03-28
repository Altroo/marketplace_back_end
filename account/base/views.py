from random import choice
from string import digits
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from dj_rest_auth.registration.views import SocialLoginView
from django.core.exceptions import SuspiciousFileOperation
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from account.base.serializers import BaseRegistrationSerializer, BasePasswordResetSerializer, \
    BaseUserEmailSerializer, BaseProfileAvatarPutSerializer, BaseProfilePutSerializer, \
    BaseProfileGETSerializer, BaseBlockUserSerializer, \
    BaseBlockedUsersListSerializer, BaseReportPostsSerializer, BaseUserAddresseDetailSerializer, \
    BaseUserAddressSerializer, BaseUserAddressesListSerializer, BaseUserAddressPutSerializer
from account.base.tasks import base_generate_user_thumbnail, base_mark_every_messages_as_read
from account.models import CustomUser, BlockedUsers, UserAddress
from os import remove
from auth_shop.base.tasks import base_generate_avatar_thumbnail
from rest_framework.pagination import PageNumberPagination
from dj_rest_auth.views import LoginView as Dj_rest_login
from dj_rest_auth.views import LogoutView as Dj_rest_logout
from chat.base.models import Status, MessageModel


class FacebookLoginView(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


class RegistrationView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def generate_random_code(length=4):
        return ''.join(choice(digits) for i in range(length))

    def post(self, request):
        password = request.data.get('password')
        password2 = request.data.get('password2')
        if password != password2:
            data = {'Error': {'password2': ["The passwords don't match."]}}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        elif len(password) < 8 or len(password2) < 8:
            data = {'Error': {'password': ["The password must be at least 8 characters long."]}}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        email = str(request.data.get('email')).lower()
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        serializer = BaseRegistrationSerializer(data={
            'email': email,
            'password': password,
            'password2': password2,
            'first_name': first_name,
            'last_name': last_name,
        })
        if serializer.is_valid():
            user = serializer.save()
            mail_subject = 'Activez votre compte'
            mail_template = 'activate_account.html'
            code = self.generate_random_code()
            message = render_to_string(mail_template, {
                'first_name': user.first_name,
                'code': code,
            })
            email = EmailMessage(
                mail_subject, message, to=(user.email,)
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)
            user.activation_code = code
            refresh = RefreshToken.for_user(user)
            data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "pk": user.pk,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            }
            # Generate user avatar and thumbnail
            base_generate_user_thumbnail.apply_async((user.pk,), )
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        email = str(request.data.get('email')).lower()
        code = request.data.get('code')
        data = {}
        try:
            user = CustomUser.objects.get(email=email)
            if user.is_active:
                data['errors'] = ["Account already activated!"]
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
            if code is not None and email is not None:
                user.is_active = True
                user.activation_code = ''
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            data['errors'] = ["Activation code invalid!"]
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            data['errors'] = ["User Doesn't exist!"]
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ResendActivationCodeView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def generate_random_code(length=4):
        return ''.join(choice(digits) for i in range(length))

    def post(self, request, *args, **kwargs):
        email = str(request.data.get('email')).lower()
        data = {}
        try:
            user = CustomUser.objects.get(email=email)
            mail_subject = 'Activez votre compte'
            mail_template = 'activate_account.html'
            # if user.activation_code:
            #    code = user.activation_code
            # else:
            code = self.generate_random_code()
            user.activation_token = code
            user.save()
            message = render_to_string(mail_template, {
                'first_name': user.first_name,
                'code': code,
            })
            email = EmailMessage(
                mail_subject, message, to=(user.email,)
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            data['email'] = ["User Doesn't exist!"]
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class SendPasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def generate_random_code(length=4):
        return ''.join(choice(digits) for i in range(length))

    def post(self, request):
        email_get = str(request.data.get('email')).lower()
        data = {}
        try:
            user = CustomUser.objects.get(email=email_get)
            if user.email is not None:
                serializer = BaseUserEmailSerializer(data=request.data)
                if serializer.is_valid():
                    # if user.password_reset_code:
                    #    code = user.password_reset_code
                    # else:
                    code = self.generate_random_code()
                    user.password_reset_code = code
                    user.save()
                    mail_subject = 'Renouvellement du mot de passe'
                    mail_template = 'password_reset.html'
                    message = render_to_string(mail_template, {
                        'first_name': user.first_name,
                        'code': code,
                    })
                    email = EmailMessage(
                        mail_subject, message, to=(user.email,)
                    )
                    email.content_subtype = "html"
                    email.send(fail_silently=False)
                    return Response(status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            data['email'] = ["User Doesn't exist!"]
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        email = str(kwargs.get('email')).lower()
        code = kwargs.get('code')
        data = {}
        try:
            user = CustomUser.objects.get(email=email)
            if code is not None and code == user.confirm_password_reset_token:
                return Response(status=status.HTTP_204_NO_CONTENT)
            data['errors'] = ['Code invalid!']
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            data['errors'] = ["User Doesn't exist!"]
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(request, *args, **kwargs):
        email = str(request.data.get('email')).lower()
        code = request.data.get('code')
        data = {}
        try:
            user = CustomUser.objects.get(email=email)
            if code is not None and email is not None and code == user.password_reset_code:
                serializer = BasePasswordResetSerializer(data=request.data)
                if serializer.is_valid():
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
            data['errors'] = ['Code invalid!']
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            data['errors'] = ["User Doesn't exist!"]
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class CheckEmailView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        email = str(request.data.get('email')).lower()
        data = {}
        try:
            CustomUser.objects.get(email=email)
            data['email'] = ['This email address already exists.']
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response(status=status.HTTP_200_OK)


class LoginView(Dj_rest_login):
    def login(self):
        super(LoginView, self).login()
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
                    'type': 'recieve_group_message',
                    'message': {
                        'type': 'status',
                        'user_pk': self.user.pk,
                        'online': True,
                        'recipient_pk': user_pk,
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
                    'type': 'recieve_group_message',
                    'message': {
                        'type': 'status',
                        'user_pk': request.user.pk,
                        'online': False,
                        'recipient_pk': user_id,
                    }
                }
                async_to_sync(channel_layer.group_send)("%s" % user_id, event)
        return super(LogoutView, self).logout(request)


class ProfileAvatarPUTView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def put(request, *args, **kwargs):
        user = CustomUser.objects.get(pk=request.user.pk)
        serializer = BaseProfileAvatarPutSerializer(data=request.data)
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
            new_avatar = serializer.update(user, serializer.validated_data)
            # Generate new avatar thumbnail
            base_generate_avatar_thumbnail.apply_async((new_avatar.pk, 'CustomUser'), )
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user_pk = kwargs.get('user_pk')
        try:
            user = CustomUser.objects.get(pk=user_pk)
            user_serializer = BaseProfileGETSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            data = {'errors': ["User Doesn't exist!"]}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(request, *args, **kwargs):
        user = CustomUser.objects.get(pk=request.user.pk)
        serializer = BaseProfilePutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(user, serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlockView(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)
    page_size = 10

    def get(self, request, *args, **kwargs):
        user_pk = request.user
        posts = BlockedUsers.objects.filter(user=user_pk)
        page = self.paginate_queryset(request=request, queryset=posts)
        if page is not None:
            serializer = BaseBlockedUsersListSerializer(instance=page, many=True)
            return self.get_paginated_response(serializer.data)

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
        user_pk = request.user
        user_blocked_pk = kwargs.get('user_pk')
        try:
            BlockedUsers.objects.get(user=user_pk, user_blocked=user_blocked_pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BlockedUsers.DoesNotExist:
            data = {'errors': ['User not found']}
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
            data = {'errors': ['Address not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def post(request, *args, **kwargs):
        user_pk = request.user.pk
        title = request.data.get('title')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        address = request.data.get('address')
        city = request.data.get('city')
        zip_code = request.data.get('zip_code')
        country = request.data.get('country')
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
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(request, *args, **kwargs):
        user_pk = request.user
        address_pk = request.data.get('address_pk')
        user_address = UserAddress.objects.get(user=user_pk, pk=address_pk)
        serializer = BaseUserAddressPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(user_address, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        user = request.user
        address_pk = kwargs.get('address_pk')
        try:
            UserAddress.objects.get(user=user, pk=address_pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserAddress.DoesNotExist:
            data = {'errors': ['Address not found.']}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class GetAllAddressesView(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)
    page_size = 10

    def get(self, request, *args, **kwargs):
        user = request.user
        posts = UserAddress.objects.filter(user=user)
        page = self.paginate_queryset(request=request, queryset=posts)
        if page is not None:
            serializer = BaseUserAddressesListSerializer(instance=page, many=True)
            return self.get_paginated_response(serializer.data)
