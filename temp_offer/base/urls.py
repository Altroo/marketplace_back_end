from django.urls import path
from .views import TempShopOfferView, GetOneTempOfferView, \
    GetTempShopOffersListView, TempShopOfferSolderView, TempShopOfferDuplicateView

app_name = 'temp_offer'

urlpatterns = [
    # Add, Edit
    # POST : Create temp product
    # PUT : Edit temp product
    # DELETE : Delete temp product
    path('', TempShopOfferView.as_view()),
    # Get : Temp product details
    path('get/<int:id_offer>', GetOneTempOfferView.as_view()),
    # Get : Temp shop products list
    path('temp_shop/<str:unique_id>', GetTempShopOffersListView.as_view()),
    # POST : add solder, PUT : update solder
    path('solder', TempShopOfferSolderView.as_view()),
    # GET : get solder, DELETE solder
    path('solder/<int:id_offer>', TempShopOfferSolderView.as_view()),
    # POST : Duplicate
    path('duplicate', TempShopOfferDuplicateView.as_view()),
]
