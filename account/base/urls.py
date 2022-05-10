from django.urls import path
from .views import FacebookLoginView, GoogleLoginView, CheckEmailView, \
    RegistrationView, ActivateAccountView, ResendActivationCodeView, \
    PasswordResetView, SendPasswordResetView, ProfileView, BlockView, \
    ReportView, LoginView, LogoutView, AddressView, GetAllAddressesView, \
    FacebookLinkingView, GoogleLinkingView, GetSocialAccountListView, \
    EncloseAccountView
# from dj_rest_auth.views import LoginView, PasswordChangeView, LogoutView
# from dj_rest_auth.views import LogoutView
from dj_rest_auth.views import PasswordChangeView
from dj_rest_auth.registration.views import SocialAccountDisconnectView
from rest_framework_simplejwt.views import TokenVerifyView
from dj_rest_auth.jwt_auth import get_refresh_view

app_name = 'account'

urlpatterns = [
    # Get facebook token
    path('facebook/', FacebookLoginView.as_view()),
    # Get google token
    path('google/', GoogleLoginView.as_view()),
    # Check if email already exists
    path('check_email/', CheckEmailView.as_view()),
    # Login with raw email/password
    path('login/', LoginView.as_view()),
    # GET : linked accounts list
    path('socials/', GetSocialAccountListView.as_view()),
    # POST : link facebook social account
    path('link_facebook/', FacebookLinkingView.as_view()),
    # POST : link google social account
    path('link_google/', GoogleLinkingView.as_view()),
    # POST : unlink social account
    # <int:pk> from socials api list
    path('unlink_social/<int:pk>/', SocialAccountDisconnectView.as_view()),
    # Logout
    path('logout/', LogoutView.as_view()),
    # Create account - verification code sent
    path('register/', RegistrationView.as_view()),
    # Activate account
    path('activate_account/', ActivateAccountView.as_view()),
    # Resend activation code
    path('resend_activation/', ResendActivationCodeView.as_view()),
    # Change password (from dj-rest-auth)
    path('password_change/', PasswordChangeView.as_view()),
    # Password reset
    path('send_password_reset/', SendPasswordResetView.as_view()),
    path('password_reset/<str:email>/<int:code>/', PasswordResetView.as_view()),
    # Tokens, Verify if token valid, Refresh access token
    path('token/verify/', TokenVerifyView.as_view()),
    path('token/refresh/', get_refresh_view().as_view()),
    # PUT : Edit image
    # path('avatar/', ProfileAvatarPUTView.as_view()),
    # PUT : Edit profil
    # GET : Get profil data include avatar
    path('profil/', ProfileView.as_view()),
    path('profil/<int:user_pk>/', ProfileView.as_view()),
    # Blocked Users
    # GET : Get blocked users list
    # POST : Block a user
    # DELETE : Unblock a user
    path('block/', BlockView.as_view()),
    path('block/<int:user_pk>/', BlockView.as_view()),
    # Repport
    # POST : Report a user
    path('report/', ReportView.as_view()),
    # Address
    # POST : Create new address
    # PUT : Edit an address
    # GET : Get one address
    # DELETE : Delete an address
    path('address/', AddressView.as_view()),
    path('address/<int:address_pk>/', AddressView.as_view()),
    # GET : Get All user addresses
    path('addresses/', GetAllAddressesView.as_view()),
    # POST : Cloturer mon compte
    path('enclose/', EncloseAccountView.as_view()),
]
