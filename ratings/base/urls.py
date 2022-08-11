from django.urls import path
from .views import GetBuyingRatingsList, \
    GetSellingRatingsList, RatingsView

app_name = 'rating'

urlpatterns = [
    # GET : Return buying ratings for a user.
    path('buyings/<int:user_pk>/', GetBuyingRatingsList.as_view()),
    # GET : Return selling ratings for a user.
    path('sellings/<int:user_pk>/', GetSellingRatingsList.as_view()),
    # POST : Add a rating.
    path('', RatingsView.as_view()),
]
