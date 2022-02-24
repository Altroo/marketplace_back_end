from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from Qaryb_API_new.settings import STATIC_ROOT, MEDIA_ROOT

urlpatterns = [
    # Account
    # Socials included (facebook, google)
    path('api/account/', include('account.base.urls', namespace='1.0.0')),
    path('api/account/', include('dj_rest_auth.urls')),
    path('api/account/registration/', include('dj_rest_auth.registration.urls')),
    # For local testing
    path('api/socials/', include('allauth.urls')),
    # Auth Shop
    path('api/shop/', include('auth_shop.base.urls', namespace='1.0.0')),
    # Temporary shops
    path('api/temp_shop/', include('temp_shop.base.urls', namespace='1.0.0')),
    # Temporary products
    path('api/temp_offer/', include('temp_offer.base.urls', namespace='1.0.0')),
    # Cities / Geo reverse
    path('api/places/', include('places.base.urls', namespace='1.0.0')),
    # path('api/version/', include('version.urls', namespace='1.0.0')),
    # Admin
    path('admin/', admin.site.urls),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': STATIC_ROOT}),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': MEDIA_ROOT}),
]
