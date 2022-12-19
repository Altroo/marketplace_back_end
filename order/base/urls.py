from django.urls import path
from .views import OrdersView, GetOrderDetailsView, CancelAllView, AcceptOrdersView

app_name = 'order'

urlpatterns = [

    # POST : Cancel order
    path('cancel/', CancelAllView.as_view()),
    # POST : Accept order
    path('accept/', AcceptOrdersView.as_view()),
    # GET : One order details. (may include several products/services)
    path('get_details/<int:order_pk>/', GetOrderDetailsView.as_view()),
    # GET : My buying orders
    path('', OrdersView.as_view()),
]
