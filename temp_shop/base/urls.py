from django.urls import path
from .views import TempShopView, \
    TempShopAvatarPutView, TempShopNamePutView, TempShopBioPutView, \
    TempShopAvailabilityPutView, TempShopContactPutView, TempShopAddressPutView, TempShopColorPutView, \
    TempShopFontPutView

app_name = 'temp_shop'

urlpatterns = [
    # Auth shop
    # POST : Create temp shop
    path('', TempShopView.as_view()),
    # GET :
    # PUT : Edit temp store
    path('edit/avatar', TempShopAvatarPutView.as_view()),
    path('edit/store_name', TempShopNamePutView.as_view()),
    path('edit/bio', TempShopBioPutView.as_view()),
    path('edit/availability', TempShopAvailabilityPutView.as_view()),
    path('edit/contact', TempShopContactPutView.as_view()),
    path('edit/address', TempShopAddressPutView.as_view()),
    path('edit/color', TempShopColorPutView.as_view()),
    path('edit/font', TempShopFontPutView.as_view()),
]
