from django.urls import path
from .views import ShopOfferView, \
    GetMyShopOffersListView, ShopOfferSolderView, ShopOfferDuplicateView, \
    GetLastThreeDeliveriesView, GetLastUsedLocalisationView, GetOfferTagsView

app_name = 'offer'

urlpatterns = [
    # GET : List of available tags : (autocomplete param : ?name_tag=A)
    path('tags/', GetOfferTagsView.as_view()),
    # GET : shop last three deliveries
    path('deliveries/<int:auth_shop_pk>/', GetLastThreeDeliveriesView.as_view()),
    # GET : Last used localisation (lon, lat + localisation name)
    path('localisation/<int:auth_shop_pk>/<str:offer_type>/', GetLastUsedLocalisationView.as_view()),
    # GET : My shop products list
    path('my_offers/', GetMyShopOffersListView.as_view()),
    # POST : Create solder,
    # PUT : Edit solder
    path('solder/', ShopOfferSolderView.as_view()),
    # GET : Get solder,
    # DELETE : Delete solder
    path('solder/<int:offer_pk>/', ShopOfferSolderView.as_view()),
    # POST : Duplicate
    path('duplicate/', ShopOfferDuplicateView.as_view()),
    # POST : Create product
    # PUT : Edit product
    # DELETE : Delete product
    # GET : product details
    path('', ShopOfferView.as_view()),
    path('<int:offer_pk>/', ShopOfferView.as_view()),
]
