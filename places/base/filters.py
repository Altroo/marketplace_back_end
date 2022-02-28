from django.utils.functional import cached_property
from django.db.models import Q
from django_filters.rest_framework import FilterSet, CharFilter
from places.base.models import City


class UserLanguageMixin:
    """
    Mixin for getting user language
    """

    default_language = 'fr'

    # @cached_property
    # def user_language(self):
    #     user_language = not isinstance(self.request.user, AnonymousUser) \
    #                     and self.request.user.lang or self.default_language
    #     return self.request.GET.get('lang', user_language).lower()

    @cached_property
    def user_language(self):
        return self.default_language


class BasePlaceFilterSet(UserLanguageMixin, FilterSet):
    """
    Base filter of places
    """

    q = CharFilter(method='search_filter')

    @staticmethod
    def search_filter(queryset, name, value):
        """
        Search by fields
        """
        if not value:
            return queryset
        query = Q(
            *[
                Q(**{f"{'_'.join(filter(None, ['name', postfix]))}__istartswith": value})
                for postfix in ['ar', 'fr', 'en', '']
            ],
            _connector=Q.OR,
        )
        return queryset.filter(query).distinct()


class CountryFilterSet(BasePlaceFilterSet):
    """
    Filter countries
    """

    pass


class CityFilterSet(BasePlaceFilterSet):
    """
    Filter cities
    """

    code = CharFilter(field_name='country__code')

    class Meta:
        model = City
        fields = (
            'code',
        )
