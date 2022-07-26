from django.urls import path
from .views import GetMyShopOffersListView, ShopOfferSolderView, ShopOfferDuplicateView, \
    GetLastThreeDeliveriesView, GetLastUsedLocalisationView, \
    GetOfferTagsView, GetOffersVuesListView, ShopOfferViewV2

app_name = 'offer'

urlpatterns = [
    # GET : List of available tags : (autocomplete param : ?name_tag=A)
    path('tags/', GetOfferTagsView.as_view()),
    # GET : shop last three deliveries
    path('deliveries/', GetLastThreeDeliveriesView.as_view()),
    path('deliveries/<uuid:unique_id>/', GetLastThreeDeliveriesView.as_view()),
    # GET : Last used localisation (lon, lat + localisation name)
    path('localisation/<str:offer_type>/', GetLastUsedLocalisationView.as_view()),
    path('localisation/<str:offer_type>/<uuid:unique_id>/', GetLastUsedLocalisationView.as_view()),
    # GET : My shop products list
    path('my_offers/', GetMyShopOffersListView.as_view()),
    path('my_offers/<uuid:unique_id>/', GetMyShopOffersListView.as_view()),
    # POST : Create solder,
    # PATCH : Edit solder
    path('solder/', ShopOfferSolderView.as_view()),
    # GET : Get solder,
    # DELETE : Delete solder
    path('solder/<int:offer_pk>/', ShopOfferSolderView.as_view()),
    # GET : Get temp solder,
    # POST : Create temp solder,
    # PATCH : Edit temp solder
    # DELETE : Delete temp solder
    path('solder/<uuid:unique_id>/<int:offer_pk>/', ShopOfferSolderView.as_view()),
    # GET : Get vues list
    path('vues/', GetOffersVuesListView.as_view()),
    # POST : Duplicate
    path('duplicate/', ShopOfferDuplicateView.as_view()),
    # POST : Create product
    # PUT : Edit product
    # DELETE : Delete product
    # GET : product details
    path('', ShopOfferViewV2.as_view()),
    path('<int:offer_pk>/', ShopOfferViewV2.as_view()),
    path('<uuid:unique_id>/<int:offer_pk>/', ShopOfferViewV2.as_view()),
    # path('backup/', ShopOfferView.as_view()),
]
