from django.urls import path
from .views import GetAvailableDefaultSeoPagesUrlsView, \
    GetSeoPageContent, GetSeoPageArticlesListView, GetSeoPageArticlesFiltersListView

app_name = 'seo_pages'

urlpatterns = [
    # GET : Get offers by slug seo page & filters
    path('offers/<slug:page_url>/', GetSeoPageArticlesListView.as_view()),
    # GET : Get seo page available filters
    path('filters/<slug:page_url>/', GetSeoPageArticlesFiltersListView.as_view()),
    # GET : all available seo page urls
    path('', GetAvailableDefaultSeoPagesUrlsView.as_view()),
    # GET : seo page content
    path('<slug:page_url>/', GetSeoPageContent.as_view()),
]
