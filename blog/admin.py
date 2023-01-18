from decouple import config
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from blog.models import Blog


class BlogAdmin(ModelAdmin):
    list_display = ('pk', 'get_page_url', 'title', 'indexed')
    search_fields = ('pk', 'page_url', 'title', 'tags', 'h_one', 'content',
                     'page_meta_description',)
    list_filter = ('indexed',)
    list_editable = ('indexed',)
    ordering = ('-pk',)
    date_hierarchy = 'created_date'

    @admin.display(description='Page url')
    def get_page_url(self, obj):
        page_url = obj.page_url
        html = f"<a href='{config('FRONT_DOMAIN')}/blog/{page_url}' target='_blank'>{page_url}</a>"
        return format_html(html)


admin.site.register(Blog, BlogAdmin)
