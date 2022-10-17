from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP
from django_filters import BaseInFilter
from django_filters import rest_framework as django_filters
from django_filters.rest_framework import FilterSet, CharFilter, \
    OrderingFilter
from django_filters.constants import EMPTY_VALUES

from offers.models import OfferTags, Offers, TempOffers


# class BaseSearchFilter(FilterSet):
#     """
#     Base search filter
#     """
#
#     search_field_kwargs = 'search'
#     search_fields = None
#     search_lookup = 'icontains'
#
#     def __init__(self, *args, **kwargs):
#         if self.search_field_kwargs and self.search_fields:
#             self.base_filters.update({
#                 self.search_field_kwargs: CharFilter(method='search_filter')
#             })
#         super().__init__(*args, **kwargs)
#
#     def search_filter(self, queryset, name, value):
#         """
#         Search by fields
#         """
#         if not value or not (self.search_field_kwargs and self.search_fields):
#             return queryset
#
#         for field in self.search_fields:
#             queryset.query.add_q(Q(**{f'{field}__{self.search_lookup}': value}, _connector=Q.OR))
#             print(queryset.query)
#         return queryset


class TagsFilterSet(FilterSet):
    """
    Base filter of tags
    """

    name_tag = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = OfferTags
        fields = ('name_tag',)


class CharInFilter(BaseInFilter, CharFilter):
    pass


# class BaseOffersListFilter(FilterSet):
#     # FILTER_DEFAULTS = ''
#     # search
#     search_field_kwargs = 'search'
#     search_lookup = 'icontains'
#     search_fields = ('title', 'description',)
#     # sort_by price
#     sort_by = OrderingFilter(fields=(
#         ('price', 'price'),
#     ))
#
#     categories = CharInFilter(method='filter_categories')
#     # categories = CharInFilter(field_name='offer_categories__name_category', lookup_expr='in', distinct=True)
#     colors = CharInFilter(method='filter_colors')
#     # colors = CharInFilter(field_name='offer_products__product_colors__code_color', lookup_expr='in', distinct=True)
#     sizes = CharInFilter(method='filter_sizes')
#     # sizes = CharInFilter(field_name='offer_products__product_sizes__code_size', lookup_expr='in', distinct=True)
#     forWhom = CharInFilter(method='filter_for_whom')
#     # forWhom = CharInFilter(field_name='for_whom__name_for_whom', lookup_expr='in', distinct=True)
#     solder = BooleanFilter(field_name='offer_solder', distinct=True)
#     labels = BooleanFilter(field_name='creator_label', distinct=True)
#     maroc = CharFilter(method='filter_maroc')
#     cities = CharInFilter(method='filter_cities')
#
#     # cities = CharInFilter(field_name='offer_delivery__delivery_city__name_fr', lookup_expr='in', distinct=True)
#
#     # def filter_queryset(self, queryset):
#     #     """
#     #     Group the fitlers by the first join table to
#     #     reduce inner join queries for performance.
#     #     This would avoid filter chaining like:
#     #     `Model.objects.filter(table_foo__id__in=[xx,xx]).filter(table_foo__name__in=[xx,xx])`
#     #     Instead, it would be grouped as:
#     #     `Model.objects.filter(table_foo__id__in=[xx,xx], table_foo__name__in=[xx,xx])`
#     #     Inspired by discussion at:
#     #     https://github.com/carltongibson/django-filter/issues/745
#     #     https://github.com/carltongibson/django-filter/pull/1167
#     #     """
#     #     groups = {
#     #
#     #     }
#     #     is_distincted = False
#     #     for name, value in self.form.cleaned_data.items():
#     #         if value in EMPTY_VALUES:
#     #             continue
#     #         f = self.filters[name]
#     #         # Do not merge Qs for customized filter method due to complexity.
#     #         if f._method or not f.__class__.filter == django_filters.Filter.filter:
#     #             queryset = self.filters[name].filter(queryset, value)
#     #             continue
#     #         # Use the joined table name as key
#     #         group_name = f.field_name.split(LOOKUP_SEP)[0]
#     #         print(group_name)
#     #         q = Q(**{LOOKUP_SEP.join([f.field_name, f.lookup_expr]): value}, _connector=Q.OR)
#     #         if f.exclude:
#     #             q = ~q
#     #         # Check if there's any join query with the same table
#     #         if group_name in groups:
#     #             print(group_name)
#     #             groups[group_name] = groups[group_name] | q
#     #             print(groups[group_name])
#     #         else:
#     #             groups[group_name] = q
#     #         print(groups)
#     #         if f.distinct:
#     #             is_distincted = True
#     #     for q in groups.values():
#     #         print(q)
#     #         queryset = queryset.filter(q)
#     #         print(queryset)
#     #     if is_distincted:
#     #         queryset = queryset.distinct()
#     #         print(queryset)
#     #     print('final query : ', queryset)
#     #     return queryset
#
#     def __init__(self, *args, **kwargs):
#         # queryset : query from views
#         # name : field_name that was set ex : made_in_label__name_fr
#         # value : value passed from query params
#         if self.search_field_kwargs and self.search_fields:
#             self.base_filters.update({
#                 self.search_field_kwargs: CharFilter(method='search_filter')
#             })
#         super().__init__(*args, **kwargs)
#
#     @staticmethod
#     def filter_categories(queryset, name, value):
#         # print('filter_categories : ', queryset)
#         if not value:
#             return queryset
#         query = Q(Q(offer_categories__name_category__in=value, _connector=Q.OR), _connector=Q.OR)
#         print(query)
#
#         return queryset.filter(query).distinct()
#
#     @staticmethod
#     def filter_colors(queryset, name, value):
#         # print('filter_colors : ', queryset)
#         if not value:
#             return queryset
#         query = Q(Q(offer_products__product_colors__code_color__in=value, _connector=Q.OR), _connector=Q.OR)
#         print(query)
#         return queryset.filter(query).distinct()
#
#     @staticmethod
#     def filter_sizes(queryset, name, value):
#         # print('filter_sizes : ', queryset)
#         if not value:
#             return queryset
#         query = Q(Q(offer_products__product_sizes__code_size__in=value, _connector=Q.OR), _connector=Q.OR)
#         print(query)
#         return queryset.filter(query).distinct()
#
#     @staticmethod
#     def filter_for_whom(queryset, name, value):
#         # print('filter_for_whom : ', queryset)
#         if not value:
#             return queryset
#         query = Q(
#             Q(for_whom__name_for_whom__in=value) |
#             Q(for_whom__code_for_whom='T'),
#             _connector=Q.OR)
#         # name, value = f'{name}__in', value
#         # return queryset.filter(**{name: value}).distinct()
#         print(query)
#         return queryset.filter(query).distinct()
#
#     @staticmethod
#     def filter_maroc(queryset, name, value):
#         # print('filter_maroc : ', queryset)
#         if not value:
#             return queryset
#         query = Q(Q(made_in_label__name_fr='Maroc', _connector=Q.OR), _connector=Q.OR)
#         print(query)
#         return queryset.filter(query).distinct()
#
#     @staticmethod
#     def filter_cities(queryset, name, value):
#         # print('filter_cities : ', queryset)
#         if not value:
#             return queryset
#         query = Q(
#             Q(offer_delivery__delivery_city__name_fr__in=value) |
#             Q(offer_delivery__all_cities=True),
#             _connector=Q.OR)
#         print(query)
#         return queryset.filter(query).distinct()
#
#     def search_filter(self, queryset, name, value):
#         """
#         Search by fields
#         """
#         # print('search_filter : ', queryset)
#         if not value or not (self.search_field_kwargs and self.search_fields):
#             return queryset
#
#         query = Q(
#             *[
#                 Q(**{f"{field}__icontains": value}, _connector=Q.OR) for field in self.search_fields
#             ],
#             _connector=Q.OR,
#         )
#         print(query)
#         return queryset.filter(query).distinct()
#
#     # class Meta:
#     #     model = Offers
#     #     fields = (
#     #         'made_in_label',
#     #     )
#     #     groups = [
#     #         RequiredGroup(['first_name', 'last_name']),
#     #     ]


# class BaseOffersListFilterV2(FilterSet):
#     # search
#     search_field_kwargs = 'search'
#     search_lookup = 'icontains'
#     search_fields = ('title', 'description',)
#     # sort_by price
#     sort_by = OrderingFilter(fields=(
#         ('price', 'price'),
#     ))
#
#     categories = CharInFilter(field_name='offer_categories__name_category', lookup_expr='in', distinct=True)
#     colors = CharInFilter(field_name='offer_products__product_colors__code_color', lookup_expr='in', distinct=True)
#     sizes = CharInFilter(field_name='offer_products__product_sizes__code_size', lookup_expr='in', distinct=True)
#     forWhom = CharInFilter(field_name='for_whom__name_for_whom', lookup_expr='in', distinct=True)
#     solder = BooleanFilter(field_name='offer_solder', distinct=True)
#     labels = BooleanFilter(field_name='creator_label', distinct=True)
#     maroc = CharFilter(method='filter_maroc')
#     cities = CharInFilter(field_name='offer_delivery__delivery_city__name_fr', lookup_expr='in', distinct=True)
#
#     filter_fields = ('categories', 'colors', 'sizes', 'forWhom', 'solder', 'labels', 'maroc', 'cities')
#
#     categories_queryset = ''
#     colors_queryset = ''
#     sizes_queryset = ''
#     forWhom_queryset = ''
#     solder_queryset = ''
#     labels_queryset = ''
#     maroc_queryset = ''
#     cities_queryset = ''
#
#     def filter_queryset(self, queryset):
#         query = []
#         sort_by = '-price'
#         for name, value in self.form.cleaned_data.items():
#             if value in EMPTY_VALUES:
#                 continue
#             match name:
#                 case 'categories':
#                     # query += Q(Q(offer_categories__name_category__in=value, _connector=Q.OR), _connector=Q.OR)
#                     name = Q(('offer_categories__name_category__in', value), _connector=Q.OR)
#                     self.categories_queryset = queryset.filter(name)
#                     query.append(name)
#                     continue
#                 case 'colors':
#                     # query += Q(offer_products__product_colors__code_color__in=value, _connector=Q.OR)
#                     # name = Q({'offer_products__product_colors__code_color__in', value}, _connector=Q.OR)
#                     name = Q(('offer_products__product_colors__code_color__in', value), _connector=Q.OR)
#                     self.colors_queryset = queryset.filter(name)
#                     query.append(name)
#                     # query[name] = value
#                     continue
#                 case 'sizes':
#                     # query += Q(offer_products__product_sizes__code_size__in=value, _connector=Q.OR)
#                     # name = Q({'offer_products__product_sizes__code_size__in', value}, _connector=Q.OR)
#                     # query[name] = value
#                     name = Q(('offer_products__product_sizes__code_size__in', value), _connector=Q.OR)
#                     self.sizes_queryset = queryset.filter(name)
#                     query.append(name)
#                     continue
#                 case 'forWhom':
#                     # query += Q(Q(for_whom__name_for_whom__in=value) | Q(for_whom__code_for_whom='T'), _connector=Q.OR)
#                     # query += Q(for_whom__name_for_whom__in=value) | Q(for_whom__code_for_whom='T')
#                     # name = Q({'for_whom__name_for_whom__in', value}, _connector=Q.OR)
#                     # query[name] = value
#                     name = Q(('for_whom__name_for_whom__in', value), _connector=Q.OR)
#                     self.forWhom_queryset = queryset.filter(name)
#                     query.append(name)
#                     continue
#                 case 'solder':
#                     # query += Q(offer_solder__exact=value)
#                     # name = Q({'offer_solder__exact', value}, _connector=Q.OR)
#                     # query[name] = value
#                     name = Q(('offer_solder__exact', value), _connector=Q.OR)
#                     self.solder_queryset = queryset.filter(name)
#                     query.append(name)
#                     continue
#                 case 'labels':
#                     # query += Q(creator_label__exact=value)
#                     # name = Q({'creator_label__exact', value}, _connector=Q.OR)
#                     # query[name] = value
#                     name = Q(('creator_label__exact', value), _connector=Q.OR)
#                     self.labels_queryset = queryset.filter(name)
#                     query.append(name)
#                     continue
#                 case 'maroc':
#                     # query += Q(Q(made_in_label__name_fr='Maroc', _connector=Q.OR), _connector=Q.OR)
#                     # query += Q(made_in_label__name_fr='Maroc', _connector=Q.OR)
#                     # name = Q({'made_in_label__name_fr', 'Maroc'}, _connector=Q.OR)
#                     # query[name] = 'Maroc'
#                     name = Q(('made_in_label__name_fr', 'Maroc'), _connector=Q.OR)
#                     self.maroc_queryset = queryset.filter(name)
#                     query.append(name)
#                     continue
#                 case 'cities':
#                     # query += Q(
#                     #     Q(offer_delivery__delivery_city__name_fr__in=value) |
#                     #     Q(offer_delivery__all_cities=True),
#                     #     _connector=Q.OR)
#                     # query += Q(offer_delivery__delivery_city__name_fr__in=value) | Q(offer_delivery__all_cities=True)
#                     # name = Q({'offer_delivery__delivery_city__name_fr__in', value}, _connector=Q.OR)
#                     # query[name] = value
#                     q_one = Q(('offer_delivery__delivery_city__name_fr__in', value), _connector=Q.OR)
#                     query.append(q_one)
#                     # name = Q({'offer_delivery__all_cities', True}, _connector=Q.OR)
#                     # query[name] = True
#                     q_two = Q(('offer_delivery__all_cities', True), _connector=Q.OR)
#                     query.append(q_two)
#                     self.cities_queryset = queryset.filter(q_one) | queryset.filter(q_two)
#                     continue
#                 case 'search':
#                     search_query = Q(
#                         *[
#                             Q(**{f"{field}__icontains": value}, _connector=Q.OR) for field in self.search_fields
#                         ],
#                         _connector=Q.OR,
#                     )
#                     query.append(search_query)
#                     continue
#                 case 'sort_by':
#                     if value:
#                         sort_by = value[0]
#                     continue
#         # final_query = *[
#         #     Q(*[i], _connector=Q.OR, ) for i in query
#         # ],
#         # for i in query:
#         # joined_query = *[Q(*[i], _connector=Q.OR, ) for i in query],
#         # results = set()
#         # for i in query:
#         #     results.add(queryset.filter(i).distinct())
#         # final_query = | + joined_query
#         # print(final_query)
#         # return results.distinct().order_by(sort_by)
#         #
#         #
#         #
#         # <QuerySet [<Offers: V - T-shirt Nike - 390.0>, <Offers: V - T-shirt Nike - 100.0>, <Offers: V - T-shirt Nike - 100.0>, <Offers: V - T-shirt Nike - 56.0>, <Offers: V - T-shirt Nike - 10.0>, <Offers: V - T-shirt Nike - 68.0>, <Offers: V - T-shirt Nike test - 100.0>, <Offers: V - test T-shirt Nike - 299.0>, <Offers: V - T-shirt Nike - 4.0>, <Offers: V - sac à dos - 100.0>, <Offers: V - T-shirt Nike - 8.0>]>
#         # <QuerySet [<Offers: V - T-shirt Nike - 100.0>]>
#         #
#
#         #
#         #
#         #
#         # Todo queryset initial vars are str
#         print(self.cities_queryset)
#         print(self.maroc_queryset)
#         print(self.colors_queryset)
#         print(self.sizes_queryset)
#         print(self.categories_queryset)
#         final_query = (
#                 [self.cities_queryset | self.maroc_queryset | self.labels_queryset | self.solder_queryset | \
#                 self.categories_queryset | self.forWhom_queryset | self.sizes_queryset | self.colors_queryset
#             ]).distinct().order_by(sort_by)
#         return final_query
#     # def __init__(self, *args, **kwargs):
#     #     # queryset : query from views
#     #     # name : field_name that was set ex : made_in_label__name_fr
#     #     # value : value passed from query params
#     #     if self.search_field_kwargs and self.search_fields:
#     #         self.base_filters.update({
#     #             self.search_field_kwargs: CharFilter(method='search_filter')
#     #         })
#     #     super().__init__(*args, **kwargs)
#     #
#     # # @staticmethod
#     # # def filter_maroc(queryset, name, value):
#     # #     # print('filter_maroc : ', queryset)
#     # #     if not value:
#     # #         return queryset
#     # #     query = Q(Q(made_in_label__name_fr='Maroc', _connector=Q.OR), _connector=Q.OR)
#     # #     print(query)
#     # #     return queryset.filter(query).distinct()
#     #
#     # def search_filter(self, queryset, name, value):
#     #     """
#     #     Search by fields
#     #     """
#     #     # print('search_filter : ', queryset)
#     #     if not value or not (self.search_field_kwargs and self.search_fields):
#     #         return queryset
#     #
#     #     query = Q(
#     #         *[
#     #             Q(**{f"{field}__icontains": value}, _connector=Q.OR) for field in self.search_fields
#     #         ],
#     #         _connector=Q.OR,
#     #     )
#     #     print(query)
#     #     return queryset.filter(query).distinct()
#
#     # class Meta:
#     #     model = Offers
#     #     fields = (
#     #         'made_in_label',
#     #     )
#     #     groups = [
#     #         RequiredGroup(['first_name', 'last_name']),
#     #     ]


class BaseOffersListSortByPrice(FilterSet):
    # sort_by price
    sort_by = OrderingFilter(fields=(
        ('price', 'price'),
    ))
    # , method='filter_price'
    # @staticmethod
    # def filter_price(queryset, name, value):
    #     if not value:
    #         return queryset
    #     else:
    #         if value == ['price']:
    #             print('in price')
    #             return queryset.order_by('price').order_by('pinned')
    #         elif value == ['-price']:
    #             print('in -price')
    #             return queryset.order_by('-price').order_by('pinned')
    #         else:
    #             # case wrong value
    #             return queryset
