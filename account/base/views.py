from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.views import ConnectionsView
from rest_framework import permissions


class FacebookLoginAccess(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLoginAccess(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    # serializer_class = BaseSocialLoginSerializer


class HomeView(ConnectionsView):
    permission_classes = (permissions.IsAuthenticated,)
    template_name = 'signup.html'
