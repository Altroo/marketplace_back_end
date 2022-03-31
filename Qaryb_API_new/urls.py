from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from Qaryb_API_new.settings import STATICFILES_DIRS, MEDIA_ROOT
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Qaryb API",
        default_version='v1',
        # description="Test description",
        # terms_of_service="https://www.google.com/policies/terms/",
        # contact=openapi.Contact(email="contact@snippets.local"),
        # license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=(permissions.IsAuthenticated,),
)

urlpatterns = [
    # API snippets
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # Account
    # Socials included (facebook, google)
    path('api/account/', include('account.base.urls', namespace='1.0.0')),
    # Needs to be activated to avoid socials connect reverse for user not active
    # Has authorized callbacks from Google console cloud & facebook developers
    path('api/socials/', include('allauth.urls')),
    # Auth Shop
    path('api/shop/', include('auth_shop.base.urls', namespace='1.0.0')),
    # Temporary shops
    path('api/temp_shop/', include('temp_shop.base.urls', namespace='1.0.0')),
    # Offers
    path('api/offer/', include('offer.base.urls', namespace='1.0.0')),
    # Temporary offers
    path('api/temp_offer/', include('temp_offer.base.urls', namespace='1.0.0')),
    # Chat
    path('api/chat/', include('chat.base.urls', namespace='1.0.0')),
    # Cities / Geo reverse
    path('api/places/', include('places.base.urls', namespace='1.0.0')),
    # path('api/version/', include('version.urls', namespace='1.0.0')),
    # Admin
    path('admin/', admin.site.urls),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': STATICFILES_DIRS}),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': MEDIA_ROOT}),
]
