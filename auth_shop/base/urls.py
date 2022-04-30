from django.urls import path
from .views import ShopView, \
    ShopAvatarPutView, ShopNamePutView, ShopBioPutView, \
    ShopAvailabilityPutView, ShopContactPutView, ShopAddressPutView, ShopColorPutView, \
    ShopFontPutView, ShopTelPutView, ShopWtspPutView, TempShopToAuthShopView, \
    ShopAskBecomeCreator, ShopQrCodeView, ShopVisitCardView

app_name = 'auth_shop'

urlpatterns = [
    # Auth shop
    # POST: Ask to become creator
    path('creator/', ShopAskBecomeCreator.as_view()),
    # POST: Transfer temp shop to auth shop
    path('transfer_shop/', TempShopToAuthShopView.as_view()),
    # PUT : Edit shop
    path('phone/', ShopTelPutView.as_view()),
    path('whatsapp/', ShopWtspPutView.as_view()),
    path('avatar/', ShopAvatarPutView.as_view()),
    path('shop_name/', ShopNamePutView.as_view()),
    path('bio/', ShopBioPutView.as_view()),
    path('availability/', ShopAvailabilityPutView.as_view()),
    path('contact/', ShopContactPutView.as_view()),
    path('address/', ShopAddressPutView.as_view()),
    path('color/', ShopColorPutView.as_view()),
    path('font/', ShopFontPutView.as_view()),
    path('qr_code/', ShopQrCodeView.as_view()),
    path('visit_card/', ShopVisitCardView.as_view()),
    # POST : Create shop
    # GET : Get shop info
    path('', ShopView.as_view()),
    path('<int:auth_shop_pk>/', ShopView.as_view()),
]
