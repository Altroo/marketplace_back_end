from django.urls import path
from .views import CartOffersView, ValidateCartOffersView, \
    GetCartOffersDetailsView, GetMyCartListView, GetServicesCoordinates

app_name = 'cart'

urlpatterns = [
    # POST : Validate my order. + Empty cart.
    path('order/', ValidateCartOffersView.as_view()),
    # GET : My cart list.
    path('all/', GetMyCartListView.as_view()),
    # GET : One or multiple product details from cart. (includes solder price)
    path('get_details/<int:shop_pk>/', GetCartOffersDetailsView.as_view()),
    # GET : Coordinates for services
    path('get_coordinates/', GetServicesCoordinates.as_view()),
    # PUT : Adjust a product from cart.
    # POST : Add product to my cart.
    path('', CartOffersView.as_view()),
    # DELETE : Remove a product from cart.
    path('<int:cart_pk>/', CartOffersView.as_view()),
]
