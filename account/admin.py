from django.contrib.auth.admin import UserAdmin
from .forms import CustomAuthShopCreationForm, CustomAuthShopChangeForm
from account.models import CustomUser
from django.contrib import admin
from rest_framework_simplejwt.token_blacklist.admin import OutstandingTokenAdmin
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken


class CustomUserAdmin(UserAdmin):
    add_form = CustomAuthShopCreationForm
    form = CustomAuthShopChangeForm
    model = CustomUser
    list_display = ('pk', 'email', 'first_name', 'last_name', 'gender',
                    'birth_date', 'city', 'country', 'phone',
                    'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'gender')
    date_hierarchy = 'date_joined'
    fieldsets = (
        ('Profile', {'fields': ('email', 'password', 'first_name', 'last_name', 'gender',
                                'birth_date', 'city', 'country', 'phone',
                                'avatar', 'avatar_thumbnail',
                                'activation_code', 'password_reset_code',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ("Date d'activité", {'fields': ('date_joined', 'last_login')}),
    )
    # add fields to the admin panel creation model
    add_fieldsets = (
        ('Profile', {'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'gender',
                                'birth_date', 'city', 'country', 'phone',
                                'avatar', 'avatar_thumbnail',
                                'activation_code', 'password_reset_code',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    search_fields = ('email',)
    ordering = ('-pk',)


class CustomOutstandingTokenAdmin(OutstandingTokenAdmin):
    def has_delete_permission(self, *args, **kwargs):
        return True


admin.site.unregister(OutstandingToken)
admin.site.register(OutstandingToken, CustomOutstandingTokenAdmin)

admin.site.register(CustomUser, CustomUserAdmin)
