from django.contrib import admin
from django.contrib.admin import ModelAdmin
from ratings.models import Ratings


class RatingsAdmin(ModelAdmin):
    list_display = ('pk', 'buyer', 'seller', 'rating_note', 'created_date')
    search_fields = ('pk', 'buyer', 'seller', 'rating_body')
    list_filter = ('rating_note',)
    ordering = ('-created_date',)


admin.site.register(Ratings, RatingsAdmin)
