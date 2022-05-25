from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import ModelAdmin
from .forms import CustomAuthShopCreationForm, CustomAuthShopChangeForm
from account.models import CustomUser, BlockedUsers, ReportedUsers, UserAddress, EnclosedAccounts
from django.contrib import admin
from rest_framework_simplejwt.token_blacklist.admin import OutstandingTokenAdmin, BlacklistedTokenAdmin
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from allauth.socialaccount.admin import SocialAccountAdmin, SocialAppAdmin, SocialTokenAdmin
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from allauth.account.models import EmailAddress


class CustomUserAdmin(UserAdmin):
    add_form = CustomAuthShopCreationForm
    form = CustomAuthShopChangeForm
    model = CustomUser
    list_display = ('pk', 'email', 'first_name', 'last_name', 'gender',
                    'birth_date', 'city', 'country',
                    'is_staff', 'is_active', 'is_enclosed')
    list_filter = ('is_staff', 'is_active', 'gender', 'is_enclosed')
    date_hierarchy = 'date_joined'
    fieldsets = (
        ('Profile', {'fields': ('email', 'password', 'first_name', 'last_name', 'gender',
                                'birth_date', 'city', 'country',
                                'avatar', 'avatar_thumbnail',
                                'activation_code', 'password_reset_code', 'is_enclosed')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ("Date d'activité", {'fields': ('date_joined', 'last_login')}),
    )
    # add fields to the admin panel creation model
    add_fieldsets = (
        ('Profile', {'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'gender',
                                'birth_date', 'city', 'country',
                                'avatar', 'avatar_thumbnail',
                                'activation_code', 'password_reset_code', 'is_enclosed')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    search_fields = ('email',)
    ordering = ('-pk',)


class CustomOutstandingTokenAdmin(OutstandingTokenAdmin):
    actions = []

    def has_delete_permission(self, *args, **kwargs):
        return True


class CustomBlockedUsersAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'user_blocked')
    search_fields = ('pk', 'user__email', 'user_blocked__email')
    ordering = ('-pk',)

    # Add permission removed
    def has_add_permission(self, *args, **kwargs):
        return False

    # Delete permission removed
    def has_delete_permission(self, *args, **kwargs):
        return False


class CustomReportedUsersAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'user_reported', 'report_reason')
    list_filter = ('report_reason',)
    search_fields = ('pk', 'user__email', 'user_reported__email')
    ordering = ('-pk',)

    # Add permission removed
    def has_add_permission(self, *args, **kwargs):
        return False

    # Delete permission removed
    def has_delete_permission(self, *args, **kwargs):
        return False


class CustomUserAddressAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'title', 'first_name',
                    'last_name', 'address', 'city',
                    'zip_code', 'country', 'phone', 'email')
    search_fields = ('pk', 'user', 'title', 'first_name', 'last_name', 'address', 'zip_code',
                     'phone', 'email')
    ordering = ('-pk',)


class CustomEnclosedAccountsAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'reason_choice', 'typed_reason')
    list_filter = ('reason_choice',)
    search_fields = ('pk', 'user__email', 'reason_choice', 'typed_reason')
    ordering = ('-pk',)

    # Add permission removed
    def has_add_permission(self, *args, **kwargs):
        return False

    # Delete permission removed
    def has_delete_permission(self, *args, **kwargs):
        return False


class CustomBlacklistedTokenAdmin(BlacklistedTokenAdmin):

    # Add permission removed
    def has_add_permission(self, *args, **kwargs):
        return False

    # Delete permission removed
    def has_delete_permission(self, *args, **kwargs):
        return False


class CustomSocialAccountAdmin(SocialAccountAdmin):

    # Add permission removed
    def has_add_permission(self, *args, **kwargs):
        return False

    # Delete permission removed
    def has_delete_permission(self, *args, **kwargs):
        return False


class CustomSocialAppAdmin(SocialAppAdmin):

    # Add permission removed
    def has_add_permission(self, *args, **kwargs):
        return False

    # Delete permission removed
    def has_delete_permission(self, *args, **kwargs):
        return False


class CustomSocialTokenAdmin(SocialTokenAdmin):

    # Add permission removed
    def has_add_permission(self, *args, **kwargs):
        return False

    # Delete permission removed
    def has_delete_permission(self, *args, **kwargs):
        return False


# Token Blacklist
admin.site.unregister(OutstandingToken)
admin.site.unregister(BlacklistedToken)
admin.site.register(OutstandingToken, CustomOutstandingTokenAdmin)
admin.site.register(BlacklistedToken, CustomBlacklistedTokenAdmin)
# Social accounts
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)
admin.site.register(SocialAccount, CustomSocialAccountAdmin)
admin.site.register(SocialApp, CustomSocialAppAdmin)
admin.site.register(SocialToken, CustomSocialTokenAdmin)
# Account
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(BlockedUsers, CustomBlockedUsersAdmin)
admin.site.register(ReportedUsers, CustomReportedUsersAdmin)
admin.site.register(UserAddress, CustomUserAddressAdmin)
admin.site.register(EnclosedAccounts, CustomEnclosedAccountsAdmin)
