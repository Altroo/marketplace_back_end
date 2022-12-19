from django.urls import path
from .views import CartOffersView, ValidateCartOffersViewV2, \
    GetCartOffersDetailsView, GetMyCartListView, GetCartCounterView, CartQuantityView

app_name = 'cart'

urlpatterns = [
    # POST : Validate my order. + Empty cart.
    path('order/<str:unique_id>/', ValidateCartOffersViewV2.as_view()),
    # GET : My cart list.
    path('all/<str:unique_id>/', GetMyCartListView.as_view()),
    path('get_cart_counter/<str:unique_id>/', GetCartCounterView.as_view()),
    # GET : One or multiple product details from cart. (includes solder price)
    path('get_details/<int:shop_pk>/<str:unique_id>/', GetCartOffersDetailsView.as_view()),
    path('quantity/<int:cart_pk>/<str:unique_id>/<str:action_type>/', CartQuantityView.as_view()),
    # POST : Add product to my cart.
    path('', CartOffersView.as_view()),
    # DELETE : Remove a product from cart.
    path('<int:cart_pk>/<str:unique_id>/', CartOffersView.as_view()),
]
