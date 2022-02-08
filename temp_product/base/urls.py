from django.urls import path
from .views import TempShopProductView, GetOneTempProductView, GetTempShopProductsListView

app_name = 'temp_product'

urlpatterns = [
    # Add, Edit
    # POST : Create temp product
    # PUT : Edit temp product
    path('', TempShopProductView.as_view()),
    # Get Temp product details
    # GET :
    path('get/<int:product_id>', GetOneTempProductView.as_view()),
    # Get Temp shop products list
    # GET :
    path('temp_shop/<str:unique_id>', GetTempShopProductsListView.as_view()),
]
