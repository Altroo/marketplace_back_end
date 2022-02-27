from django.urls import path
from .views import FacebookLoginAccess, GoogleLoginAccess, \
    CheckEmailView, RegistrationView, ActivateAccountView, \
    ResendActivationCodeView, PasswordResetView, SendPasswordResetView
from dj_rest_auth.views import LoginView, PasswordChangeView, LogoutView
from rest_framework_simplejwt.views import TokenVerifyView
from dj_rest_auth.jwt_auth import get_refresh_view

app_name = 'account'

urlpatterns = [
    # Get facebook token
    path('facebook_access/', FacebookLoginAccess.as_view()),
    # Get google token
    path('google_access/', GoogleLoginAccess.as_view()),
    # Check if email already exists
    path('check_email/', CheckEmailView.as_view()),
    # Login with raw email/password
    path('login/', LoginView.as_view()),
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
]
