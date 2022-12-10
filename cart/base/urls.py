from django.urls import path
from .views import CartOffersView, ValidateCartOffersView, \
    GetCartOffersDetailsView, GetMyCartListView

app_name = 'cart'

urlpatterns = [
    # POST : Validate my order. + Empty cart.
    path('order/<str:unique_id>/', ValidateCartOffersView.as_view()),
    # GET : My cart list.
    path('all/<str:unique_id>/', GetMyCartListView.as_view()),
    # GET : One or multiple product details from cart. (includes solder price)
    path('get_details/<int:shop_pk>/<str:unique_id>/', GetCartOffersDetailsView.as_view()),
    # GET : Get coordinates for services
    # path('get_coordinates/', GetServicesCoordinates.as_view()),
    # PATCH : Adjust a product from cart.
    # POST : Add product to my cart.
    path('', CartOffersView.as_view()),
    # DELETE : Remove a product from cart.
    path('<int:cart_pk>/<str:unique_id>/', CartOffersView.as_view()),
]
