from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomAuthShopCreationForm, CustomAuthShopChangeForm
from .models import AuthShop, Categories
from django.contrib.admin import ModelAdmin


class CustomAuthShopAdmin(UserAdmin):
    add_form = CustomAuthShopCreationForm
    form = CustomAuthShopChangeForm
    model = AuthShop
    list_display = ('pk', 'shop_name', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', ("avatar", admin.EmptyFieldListFilter))
    date_hierarchy = 'created_date'
    fieldsets = (
        ('Profile',
         {'fields': ('shop_name', 'password',
                     'avatar', 'color_code',
                     'font_name', 'bio',
                     'opening_days',
                     'morning_hour_from', 'morning_hour_to',
                     'afternoon_hour_from', 'afternoon_hour_to',
                     'phone', 'contact_email', 'website_link',
                     'facebook_link', 'twitter_link', 'instagram_link', 'whatsapp',
                     'zone_by', 'longitude', 'latitude', 'address_name', 'km_radius',
                     'qaryb_link')}),
        ('Permissions',
         {'fields': ('is_active', 'is_staff',
                     'is_superuser')}),
        ("Date d'activité",
         {'fields': ('created_date', 'last_login')}),
    )
    # add fields to the admin panel creation model
    add_fieldsets = (
        ('Profile',
         {'fields': ('shop_name', 'password1', 'password2',
                     'avatar', 'color_code',
                     'font_name', 'bio',
                     'opening_days',
                     'morning_hour_from', 'morning_hour_to',
                     'afternoon_hour_from', 'afternoon_hour_to',
                     'phone', 'contact_email', 'website_link',
                     'facebook_link', 'twitter_link', 'instagram_link', 'whatsapp',
                     'zone_by', 'longitude', 'latitude', 'address_name', 'km_radius',
                     'qaryb_link')}),
        ('Permissions',
         {'fields': ('is_active', 'is_staff',
                     'is_superuser')}),
    )
    search_fields = ('email',)
    ordering = ('-pk',)


class CustomCategoriesAdmin(ModelAdmin):
    list_display = ('pk', 'code_category', 'name_category',)
    search_fields = ('pk', 'code_category', 'name_category',)
    ordering = ('pk',)


admin.site.register(AuthShop, CustomAuthShopAdmin)
admin.site.register(Categories, CustomCategoriesAdmin)
