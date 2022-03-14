from django.urls import path
from .views import ShopOfferView, GetOneOfferView, \
    GetShopOffersListView, ShopOfferSolderView, ShopOfferDuplicateView, \
    GetLastThreeDeliveriesView, GetLastUsedLocalisationView

app_name = 'offer'

urlpatterns = [
    # Add, Edit
    # POST : Create product
    # PUT : Edit product
    # DELETE : Delete product
    path('', ShopOfferView.as_view()),
    # GET : product details
    path('get/<int:offer_id>/', GetOneOfferView.as_view()),
    # GET : shop products list
    path('deliveries/get/<int:auth_shop_pk>/', GetLastThreeDeliveriesView.as_view()),
    # GET : Last used localisation (lon, lat + localisation name)
    path('localisation/get/<str:unique_id>/<str:offer_type>/', GetLastUsedLocalisationView.as_view()),
    # GET : My shop products list
    path('shop/', GetShopOffersListView.as_view()),
    # POST : add solder, PUT : update solder
    path('solder/', ShopOfferSolderView.as_view()),
    # GET : get solder, DELETE solder
    path('solder/<int:offer_id>/', ShopOfferSolderView.as_view()),
    # POST : Duplicate
    path('duplicate/', ShopOfferDuplicateView.as_view()),
]
