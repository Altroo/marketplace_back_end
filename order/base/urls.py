from django.urls import path
from .views import GetMySellingOrdersListView, GetMyBuyingsOrdersListView, \
    GetMyOrderDetailsView, CancelOneOrderView, CancelAllView, AcceptOrdersView, \
    PatchOrderStatusView, AdjustDeliveryPriceView, AcceptNewAdjustedDeliveryPrice

app_name = 'order'

urlpatterns = [
    # GET : My buying orders
    path('buyings/', GetMyBuyingsOrdersListView.as_view()),
    # GET : My selling orders
    path('sellings/', GetMySellingOrdersListView.as_view()),
    # GET : One order details. (may include several products) + mark viewed_buyer as True
    path('get_details/<str:order_type>/<int:order_pk>/', GetMyOrderDetailsView.as_view()),
    # POST : Cancel a product from an order (Seller & Buyer)
    path('cancel_one/', CancelOneOrderView.as_view()),
    # POST : Cancel everything (Seller & Buyer)
    path('cancel_all/', CancelAllView.as_view()),
    # POST : Accept one or grouped orders (Buyer)
    path('accept/', AcceptOrdersView.as_view()),
    # POST : Upgrade order status to Ready or Shipped
    path('ready_shipped/', PatchOrderStatusView.as_view()),
    # POST : Adjust delivery price (Seller)
    path('adjust_delivery_price/', AdjustDeliveryPriceView.as_view()),
    # POST : Accept the new delivery price (Buyer)
    path('accept_delivery_price/', AcceptNewAdjustedDeliveryPrice.as_view()),
    # App ratings
    # POST : Rate the buyer + Change status to "to rate" for other party
    # GET : My ratings list. (Buy, Sells)
]
