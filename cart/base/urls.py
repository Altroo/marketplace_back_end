from django.urls import path
from .views import CartOffersView, ValidateCartOffersView, GetMyCartListView, GetCartOffersView, \
    GetCartOffersDeliveriesView

app_name = 'cart'

urlpatterns = [
    # POST : Validate my order. + Empty cart.
    path('order/', ValidateCartOffersView.as_view()),
    # GET : My cart list.
    path('all/', GetMyCartListView.as_view()),
    # GET : One or multiple product details from cart. (includes solder price)
    path('get/<str:offer_pks>/', GetCartOffersView.as_view()),
    path('get_details/<str:offer_pks>/', GetCartOffersDeliveriesView.as_view()),
    # PUT : Adjust a product from cart.
    # POST : Add product to my cart.
    path('', CartOffersView.as_view()),
    # DELETE : Remove a product from cart.
    path('<int:cart_pk>/', CartOffersView.as_view()),
]
