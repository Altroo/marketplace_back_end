from django.urls import path
from .views import GetMyOrdersListView

app_name = 'order'

urlpatterns = [
    # GET : My orders list.
    path('', GetMyOrdersListView.as_view()),
    # GET : One order details. (may include several products) + mark viewed_buyer as True
    # POST : Cancel a product from an order (Seller)
    # POST : Cancel a product from an order (Buyer)
    # POST : Cancel everything (Seller)
    # POST : Cancel everything (Buyer)
    # POST : Accept an order (Buyer)
    # PUT : Adjust delivery price (Seller)
    # POST : Accept the new delivery price (Buyer)
    # PUT : Change status to shipped (Buyer)
    # App ratings
    # POST : Rate the buyer + Change status to "to rate" for other party
    # GET : My ratings list. (Buy, Sells)
]
