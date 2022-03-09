from django.urls import path
from .views import ShopView, \
    ShopAvatarPutView, ShopNamePutView, ShopBioPutView, \
    ShopAvailabilityPutView, ShopContactPutView, ShopAddressPutView, ShopColorPutView, \
    ShopFontPutView, ShopTelPutView, ShopWtspPutView, TempShopToAuthShopView

app_name = 'auth_shop'

urlpatterns = [
    # Auth shop
    # POST : Create  shop
    # GET : Get  shop info
    path('', ShopView.as_view()),
    path('transfer_shop/', TempShopToAuthShopView.as_view()),
    path('get/<int:pk>/', ShopView.as_view()),
    path('add/phone/', ShopTelPutView.as_view()),
    path('add/whatsapp/', ShopWtspPutView.as_view()),
    # PUT : Edit  store
    path('edit/avatar/', ShopAvatarPutView.as_view()),
    path('edit/store_name/', ShopNamePutView.as_view()),
    path('edit/bio/', ShopBioPutView.as_view()),
    path('edit/availability/', ShopAvailabilityPutView.as_view()),
    path('edit/contact/', ShopContactPutView.as_view()),
    path('edit/address/', ShopAddressPutView.as_view()),
    path('edit/color/', ShopColorPutView.as_view()),
    path('edit/font/', ShopFontPutView.as_view()),
]
