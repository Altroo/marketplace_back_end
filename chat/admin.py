from django.contrib.admin import ModelAdmin, site
from chat.base.models import MessageModel, Status, ArchivedConversations


class MessagesAdmin(ModelAdmin):
    readonly_fields = ('created', )
    search_fields = ('id', 'body', 'user__email', 'recipient__email')
    list_display = ('id', 'user', 'viewed', 'recipient', 'body', 'created')
    list_display_links = ('id',)
    list_filter = ('viewed', )
    date_hierarchy = 'created'
    ordering = ('-pk',)


class StatusAdmin(ModelAdmin):
    list_display = ('pk', 'user',
                    'last_update', 'online')
    list_filter = ('online',)
    search_fields = ('pk', 'user__email')
    ordering = ('-pk',)


class ArchivedConversationsAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'recipient')
    search_fields = ('pk', 'user__email', 'recipient__email')
    ordering = ('-pk',)


site.register(MessageModel, MessagesAdmin)
site.register(Status, StatusAdmin)
site.register(ArchivedConversations, ArchivedConversationsAdmin)
