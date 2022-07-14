from django.urls import path
from .views import ShopView, \
    ShopAvatarPutView, ShopNamePutView, ShopBioPutView, \
    ShopAvailabilityPutView, ShopContactPutView, ShopAddressPutView, ShopColorPutView, \
    ShopFontPutView, ShopTelPutView, ShopWtspPutView, TempShopToAuthShopView, \
    ShopAskBecomeCreator, ShopQrCodeView, \
    ShopModeVacanceView, ShopGetPhoneCodesView

app_name = 'shop'

urlpatterns = [
    # Auth shop + Temp shop
    # GET : All available phone codes
    path('phone_codes/', ShopGetPhoneCodesView.as_view()),
    # POST: Ask to become creator
    path('creator/', ShopAskBecomeCreator.as_view()),
    # POST: Transfer temp shop to auth shop
    path('transfer_shop/', TempShopToAuthShopView.as_view()),
    # PATCH : Edit shop
    path('phone/', ShopTelPutView.as_view()),
    path('whatsapp/', ShopWtspPutView.as_view()),
    path('avatar/', ShopAvatarPutView.as_view()),
    # TODO change it to just name
    path('shop_name/', ShopNamePutView.as_view()),
    path('bio/', ShopBioPutView.as_view()),
    path('availability/', ShopAvailabilityPutView.as_view()),
    path('contact/', ShopContactPutView.as_view()),
    path('address/', ShopAddressPutView.as_view()),
    path('color/', ShopColorPutView.as_view()),
    path('font/', ShopFontPutView.as_view()),
    # POST : generate qr code
    # GET : get qr code
    path('qr_code/', ShopQrCodeView.as_view()),
    # path('visit_card/', ShopVisitCardView.as_view()),
    # GET : get mode vacance
    # POST : add mode vacance
    # PATCH : update mode vacance
    # DELETE : delete mode vacance
    path('mode_vacance/', ShopModeVacanceView.as_view()),
    # path('unique_id_verify/', ShopUniqueIDVerifyView.as_view()),
    # POST : Create shop
    # GET : Get shop info
    path('', ShopView.as_view()),
    path('<uuid:unique_id>/', ShopView.as_view()),
    path('<slug:shop_link>/', ShopView.as_view()),
]
