from django.urls import path
from .views import FacebookLoginAccess, GoogleLoginAccess, \
    CheckEmailView, RegistrationView, ActivateAccountView, \
    ResendActivationCodeView, PasswordResetView, SendPasswordResetView
from dj_rest_auth.views import LoginView, LogoutView, PasswordChangeView
from rest_framework_simplejwt.views import TokenVerifyView
from dj_rest_auth.jwt_auth import get_refresh_view

app_name = 'account'

urlpatterns = [
    # Get facebook token
    path('facebook-access/', FacebookLoginAccess.as_view()),
    # Get google token
    path('google-access/', GoogleLoginAccess.as_view()),
    # Check if email already exists
    path('check-email/', CheckEmailView.as_view()),
    # Login with raw email/password
    path('login/', LoginView.as_view()),
    # Logout
    path('logout/', LogoutView.as_view()),
    # Create account - verification code sent
    path('register/', RegistrationView.as_view()),
    # Activate account
    path('activate-account/<str:email>/<int:code>/', ActivateAccountView.as_view(), name='activate_account'),
    # Resend activation code
    path('resend-activation/', ResendActivationCodeView.as_view()),
    # Change password (from dj-rest-auth)
    path('password-change/', PasswordChangeView.as_view()),
    # Password reset
    path('send-password-reset/', SendPasswordResetView.as_view()),
    path('password-reset/<str:email>/<int:code>/', PasswordResetView.as_view(), name='password_reset'),
    # Tokens, Verify if token valid, Refresh access token
    path('token/verify/', TokenVerifyView.as_view()),
    path('token/refresh/', get_refresh_view().as_view()),
]
