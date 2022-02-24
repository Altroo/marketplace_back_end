from django.urls import path, include
from .views import FacebookLoginAccess, GoogleLoginAccess, HomeView

app_name = 'account'

urlpatterns = [
    # TOKENS
    # verify token : token/verify/
    # refresh access token : token/refresh/

    # User auth
    # Send email password reset : password/reset/
    # Resend password reset email confirmed : password/reset/confirm/
    # Change password : password/change/
    # Login with email : login/
    # URLs that require a user to be logged in with a valid session / token.
    # Logout : logout/
    # Get user details : user/
    # path('', include('dj_rest_auth.urls')),
    # Registration emails
    # Create new account : registration/
    # Verify email : registration/verify-email
    # Resend verification email : registration/resend-email
    # Confirm email : registration/account-confirm-email/<keyn>
    # UNKNOWN : registration/account-email-verification-sent/
    # path('registration/', include('dj_rest_auth.registration.urls')),
    # Socials
    # path('check-account/', CheckAccountView.as_view()),
    path('facebook-access/', FacebookLoginAccess.as_view(), name='fb_login_access'),
    path('google-access/', GoogleLoginAccess.as_view(), name='fb_login_access'),
    # path('connections/', ConnectionsRestView.as_view(), name='connections'),
    path('home/', HomeView.as_view()),
]
