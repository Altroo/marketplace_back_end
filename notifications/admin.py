from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Notifications


class CustomNotificationsAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'type', 'viewed', 'created_date')
    search_fields = ('pk', 'user__email')
    list_filter = ('type', 'viewed')
    date_hierarchy = 'created_date'
    ordering = ('-pk',)


admin.site.register(Notifications, CustomNotificationsAdmin)
