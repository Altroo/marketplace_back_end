from django.urls import path
from .views import TempShopView, \
    TempShopAvatarPutView, TempShopNamePutView, TempShopBioPutView, \
    TempShopAvailabilityPutView, TempShopContactPutView, TempShopAddressPutView, TempShopColorPutView, \
    TempShopFontPutView, TempShopTelPutView, TempShopWtspPutView, TempShopGetPhoneCodesView

app_name = 'temp_shop'

urlpatterns = [
    # Temp shop
    # POST : Create temp shop
    # GET : Get temp shop info
    path('', TempShopView.as_view()),
    path('<str:unique_id>/', TempShopView.as_view()),
    # GET : All available phone codes
    path('phone_codes/', TempShopGetPhoneCodesView.as_view()),
    # PUT : Edit temp store
    path('phone/', TempShopTelPutView.as_view()),
    path('whatsapp/', TempShopWtspPutView.as_view()),
    path('avatar/', TempShopAvatarPutView.as_view()),
    path('store_name/', TempShopNamePutView.as_view()),
    path('bio/', TempShopBioPutView.as_view()),
    path('availability/', TempShopAvailabilityPutView.as_view()),
    path('contact/', TempShopContactPutView.as_view()),
    path('address/', TempShopAddressPutView.as_view()),
    path('color/', TempShopColorPutView.as_view()),
    path('font/', TempShopFontPutView.as_view()),
]
