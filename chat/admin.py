from django.contrib.admin import ModelAdmin, site
from chat.base.models import MessageModel, Status


class MessageModelAdmin(ModelAdmin):
    readonly_fields = ('created', 'viewed_timestamp')
    search_fields = ('id', 'body', 'user__email', 'recipient__email')
    list_display = ('id', 'user', 'viewed', 'recipient', 'body', 'created',
                    'viewed_timestamp')
    list_display_links = ('id',)
    list_filter = ('viewed', )
    date_hierarchy = 'created'
    ordering = ('-pk',)


class CustomStatusAdmin(ModelAdmin):
    list_display = ('pk', 'user',
                    'last_update', 'online')
    list_filter = ('online',)
    search_fields = ('pk', 'user__email')
    ordering = ('-pk',)


site.register(MessageModel, MessageModelAdmin)
site.register(Status, CustomStatusAdmin)
