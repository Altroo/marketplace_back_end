from django.urls import path
from .views import TempShopProductView, GetOneTempProductView, \
    GetTempShopProductsListView, TempShopProductSolderView, TempShopProductDuplicateView

app_name = 'temp_product'

urlpatterns = [
    # Add, Edit
    # POST : Create temp product
    # PUT : Edit temp product
    path('', TempShopProductView.as_view()),
    # Get : Temp product details
    path('get/<int:product_id>', GetOneTempProductView.as_view()),
    # Get : Temp shop products list
    path('temp_shop/<str:unique_id>', GetTempShopProductsListView.as_view()),
    # POST : add solder, PUT : update solder
    path('solder', TempShopProductSolderView.as_view()),
    # GET : get solder, DELETE solder
    path('solder/<int:temp_product_id>', TempShopProductSolderView.as_view()),
    # POST : Duplicate
    path('duplicate', TempShopProductDuplicateView.as_view()),
]
