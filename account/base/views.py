from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from account.models import CustomUser
from account.base.serializers import BaseRegistrationSerializer, BasePasswordResetSerializer, \
    BaseUserEmailSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from random import choice
from string import digits


class FacebookLoginAccess(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLoginAccess(SocialLoginView):
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
