from django.urls import path
from .views import GetMySellingOrdersListView, GetMyBuyingsOrdersListView, \
    GetMyOrderDetailsViewV2, CancelSellingOfferView, CancelBuyingOfferView

app_name = 'order'

urlpatterns = [
    # GET : My orders list.
    # GET : My buying orders
    path('buyings/', GetMyBuyingsOrdersListView.as_view()),
    # GET : My selling orders
    path('sellings/', GetMySellingOrdersListView.as_view()),
    # GET : One order details. (may include several products) + mark viewed_buyer as True
    path('get_details/<str:order_type>/<int:order_pk>/', GetMyOrderDetailsViewV2.as_view()),
    # POST : Cancel a product from an order (Seller)
    path('cancel_sell/', CancelSellingOfferView.as_view()),
    # POST : Cancel a product from an order (Buyer)
    path('cancel_buy/', CancelBuyingOfferView.as_view()),
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
