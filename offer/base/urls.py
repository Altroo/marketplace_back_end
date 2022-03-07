from django.urls import path
from .views import ShopOfferView, GetOneOfferView, \
    GetShopOffersListView, ShopOfferSolderView, ShopOfferDuplicateView

app_name = 'offer'

urlpatterns = [
    # Add, Edit
    # POST : Create product
    # PUT : Edit product
    # DELETE : Delete product
    path('', ShopOfferView.as_view()),
    # Get : product details
    path('get/<int:id_offer>/', GetOneOfferView.as_view()),
    # Get : shop products list
    path('shop/', GetShopOffersListView.as_view()),
    # POST : add solder, PUT : update solder
    path('solder/', ShopOfferSolderView.as_view()),
    # GET : get solder, DELETE solder
    path('solder/<int:id_offer>/', ShopOfferSolderView.as_view()),
    # POST : Duplicate
    path('duplicate/', ShopOfferDuplicateView.as_view()),
]
