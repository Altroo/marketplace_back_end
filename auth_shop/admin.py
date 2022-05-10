from django.contrib import admin
from auth_shop.base.models import AuthShopDays, AuthShop, \
    PhoneCodes, AskForCreatorLabel, ModeVacance
from django.contrib.admin import ModelAdmin


class CustomAuthShopAdmin(ModelAdmin):
    list_display = ('pk', 'shop_name', 'user', 'creator')
    search_fields = ('pk', 'shop_name', 'user')
    list_filter = ('creator',)
    ordering = ('-pk',)


class CustomDaysAdmin(ModelAdmin):
    list_display = ('pk', 'code_day', 'name_day',)
    search_fields = ('pk', 'code_day', 'name_day',)
    ordering = ('pk',)


class CustomPhoneCodesAdmin(ModelAdmin):
    list_display = ('pk', 'phone_code')
    search_fields = ('pk', 'phone_code')
    ordering = ('-pk',)


class CustomAskForCreatorLabelAdmin(ModelAdmin):
    list_display = ('pk', 'auth_shop', 'status', 'asked_counter', 'created_date', 'updated_date')
    list_editable = ('status',)
    search_fields = ('pk', 'auth_shop__shop_name')
    list_filter = ('status',)
    ordering = ('-pk',)
    date_hierarchy = 'created_date'

    def save_model(self, request, obj, form, change):
        auth_shop = AuthShop.objects.get(pk=obj.auth_shop.pk)
        # Confirmed
        if obj.status == 'C':
            auth_shop.creator = True
        # Rejected
        elif obj.status == 'R':
            auth_shop.creator = False
        # Default : Awaiting confirmation
        else:
            auth_shop.creator = False
        auth_shop.save()
        super(CustomAskForCreatorLabelAdmin, self).save_model(request, obj, form, change)

    # Add permission removed
    def has_add_permission(self, *args, **kwargs):
        return False

    # Delete permission removed
    def has_delete_permission(self, *args, **kwargs):
        return False


class CustomModeVacanceAdmin(ModelAdmin):
    list_display = ('pk', 'auth_shop', 'date_from', 'date_to')
    search_fields = ('pk', 'auth_shop', 'date_from', 'date_to')
    ordering = ('-pk',)


admin.site.register(AuthShop, CustomAuthShopAdmin)
admin.site.register(AuthShopDays, CustomDaysAdmin)
admin.site.register(PhoneCodes, CustomPhoneCodesAdmin)
admin.site.register(AskForCreatorLabel, CustomAskForCreatorLabelAdmin)
admin.site.register(ModeVacance, CustomModeVacanceAdmin)
