from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import AuthShop


class CustomAuthShopCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = AuthShop
        fields = ('email',)


class CustomAuthShopChangeForm(UserChangeForm):

    class Meta:
        model = AuthShop
        fields = ('email',)

