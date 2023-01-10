from django.urls import path
from .views import GetAvailableBlogPageUrlsView, GetBlogPageContent

app_name = 'blog'

urlpatterns = [
    # GET : all available blog urls
    path('', GetAvailableBlogPageUrlsView.as_view()),
    #
    # GET : seo page content
    path('<slug:page_url>/', GetBlogPageContent.as_view()),
]
