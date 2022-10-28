from django.urls import path
from .views import AvailableSubscriptionView, SubscriptionView, \
    PromoCodeView, GetUserSubscriptionView, GetUserIndexedArticlesView, \
    GetUserAvailableArticlesView

app_name = 'subscription'

urlpatterns = [
    path('', SubscriptionView.as_view()),
    path('<int:nbr_article>/', SubscriptionView.as_view()),
    path('user_subscription/', GetUserSubscriptionView.as_view()),
    path('check_promo_code/', PromoCodeView.as_view()),
    path('available_subscription/', AvailableSubscriptionView.as_view()),
    # root - get - post
    path('indexed_articles/', GetUserIndexedArticlesView.as_view()),
    path('available_articles/', GetUserAvailableArticlesView.as_view()),
    # Delete
    path('indexed_articles/<str:indexed_article_pk>', GetUserIndexedArticlesView.as_view()),

]
