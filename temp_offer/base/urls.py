from django.urls import path
from .views import TempShopOfferView, \
    GetTempShopOffersListView, TempShopOfferSolderView, TempShopOfferDuplicateView, \
    GetLastThreeTempDeliveriesView, GetLastTempUsedLocalisationView

app_name = 'temp_offer'

urlpatterns = [
    # GET : Last three temp deliveries
    path('deliveries/<str:unique_id>/', GetLastThreeTempDeliveriesView.as_view()),
    # GET : Last used localisation (lon, lat + localisation name)
    path('localisation/<str:unique_id>/<str:temp_offer_type>/', GetLastTempUsedLocalisationView.as_view()),
    # GET : My Temp shop products list
    path('my_offers/<str:unique_id>/', GetTempShopOffersListView.as_view()),
    # POST : Create solder,
    # PUT : Edit solder
    path('solder/', TempShopOfferSolderView.as_view()),
    # GET : Get solder,
    # DELETE : Delete solder
    path('solder/<str:unique_id>/<int:temp_offer_pk>/', TempShopOfferSolderView.as_view()),
    # POST : Duplicate
    path('duplicate/', TempShopOfferDuplicateView.as_view()),
    # POST : Create temp product
    # PUT : Edit temp product
    # DELETE : Delete temp product
    # GET : Get Temp product details
    path('', TempShopOfferView.as_view()),
    path('<int:temp_offer_pk>/', TempShopOfferView.as_view()),
]
