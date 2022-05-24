from django_filters.rest_framework import FilterSet, CharFilter
from offer.base.models import OfferTags


class TagsFilterSet(FilterSet):
    """
    Base filter of tags
    """

    name_tag = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = OfferTags
        fields = ['name_tag']