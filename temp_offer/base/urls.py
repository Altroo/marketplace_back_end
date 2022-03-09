from django.urls import path
from .views import TempShopOfferView, GetOneTempOfferView, \
    GetTempShopOffersListView, TempShopOfferSolderView, TempShopOfferDuplicateView, \
    GetLastThreeTempDeliveriesView, GetLastTempUsedLocalisationView

app_name = 'temp_offer'

urlpatterns = [
    # Add, Edit
    # POST : Create temp product
    # PUT : Edit temp product
    # DELETE : Delete temp product
    path('', TempShopOfferView.as_view()),
    # GET : Temp product details
    path('get/<int:temp_offer_id>/', GetOneTempOfferView.as_view()),
    # GET : Last three temp deliveries
    path('temp_deliveries/get/<str:unique_id>/', GetLastThreeTempDeliveriesView.as_view()),
    # GET : Last used localisation (lon, lat + localisation name)
    path('temp_localisation/get/<str:unique_id>/<str:temp_offer_type>/', GetLastTempUsedLocalisationView.as_view()),
    # GET : Temp shop products list
    path('temp_shop/<str:unique_id>/', GetTempShopOffersListView.as_view()),
    # POST : add solder, PUT : update solder
    path('solder/', TempShopOfferSolderView.as_view()),
    # GET : get solder, DELETE solder
    path('solder/<int:temp_offer_id>/', TempShopOfferSolderView.as_view()),
    # POST : Duplicate
    path('duplicate/', TempShopOfferDuplicateView.as_view()),
]
