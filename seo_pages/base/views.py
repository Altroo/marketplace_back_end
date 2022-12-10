from typing import Union
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from offers.base.filters import BaseOffersListSortByPrice
from offers.models import Offers
from seo_pages.base.serializers import BaseDefaultSeoPageSerializer, BaseDefaultSeoPageUrlsOnlySerializer
from seo_pages.models import DefaultSeoPage
from offers.base.serializers import BaseOffersListSerializer


class GetAvailableDefaultSeoPagesUrlsView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        default_seo_pages = DefaultSeoPage.objects.filter(indexed=True)
        serializer = BaseDefaultSeoPageUrlsOnlySerializer(default_seo_pages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetSeoPageContent(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        page_url = kwargs.get('page_url')
        try:
            default_seo_page = DefaultSeoPage.objects.get(page_url=page_url)
            serializer = BaseDefaultSeoPageSerializer(default_seo_page)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DefaultSeoPage.DoesNotExist:
            errors = {"errors": ["Collection not found."]}
            raise ValidationError(errors)


class GetSeoPageArticlesFiltersListView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        page_url: str = self.kwargs['page_url']
        available_categories = set()
        available_colors = set()
        available_sizes = set()
        available_for_whom = set()
        available_solder = False
        available_labels = False
        available_made_in_maroc = False
        available_cities = set()
        available_services = False
        try:
            seo_page = DefaultSeoPage.objects.get(page_url=page_url)
            articles = seo_page.articles.filter(status__in=['I', 'U']) \
                .select_related('offer__offer_products', 'offer__offer_services', 'offer__offer_solder') \
                .prefetch_related('offer__offer_categories', 'offer__for_whom', 'offer__made_in_label',
                                  'offer__offer_delivery')
            offers = []
            for article in articles:
                offers.append(article.offer)
            offer: Union[QuerySet, Offers]
            for offer in offers:
                if offer.offer_type == 'V':
                    product_categories = offer.offer_categories.values_list('code_category', flat=True).all()
                    product_colors = offer.offer_products.product_colors.values_list('code_color', flat=True).all()
                    product_sizes = offer.offer_products.product_sizes.values_list('code_size', flat=True).all()
                    for_whom = offer.for_whom.values_list('code_for_whom', flat=True).all()
                    if available_solder:
                        solder = available_solder
                    else:
                        try:
                            _ = offer.offer_solder
                            solder = True
                        except ObjectDoesNotExist:
                            solder = False
                    if available_labels:
                        labels = available_labels
                    else:
                        labels = offer.creator_label
                    if available_made_in_maroc:
                        made_in_maroc = available_made_in_maroc
                    else:
                        if offer.made_in_label is not None:
                            made_in_maroc = True if offer.made_in_label.name_fr == 'Maroc' else False
                        else:
                            made_in_maroc = False
                    cities = offer.offer_delivery.values_list('delivery_city__name_fr', flat=True).all()
                    for i in product_categories:  # type: str
                        available_categories.add(i)
                    for i in product_colors:
                        available_colors.add(i)
                    for i in product_sizes:
                        available_sizes.add(i)
                    for i in for_whom:
                        available_for_whom.add(i)
                    available_solder = solder
                    available_labels = labels
                    available_made_in_maroc = made_in_maroc
                    for i in cities:
                        if i is not None:
                            available_cities.add(i)
                elif offer.offer_type == 'S':
                    available_services = True
            data = {
                'available_categories': available_categories,
                'available_colors': available_colors,
                'available_sizes': available_sizes,
                'available_for_whom': available_for_whom,
                'available_solder': available_solder,
                'available_labels': available_labels,
                'available_made_in_maroc': available_made_in_maroc,
                'available_cities': available_cities,
                'available_services': available_services,
            }
            return Response(data, status=status.HTTP_200_OK)
        except DefaultSeoPage.DoesNotExist:
            errors = {"error": ["Page not found."]}
            raise ValidationError(errors)


class GetSeoPageArticlesListView(ListAPIView, PageNumberPagination):
    permission_classes = (permissions.AllowAny,)
    page_size = 10
    filterset_class = BaseOffersListSortByPrice
    http_method_names = ('get',)
    serializer_class = BaseOffersListSerializer

    def get_queryset(self) -> Union[QuerySet, None]:
        page_url: str = self.kwargs['page_url']
        try:
            seo_page = DefaultSeoPage.objects.get(page_url=page_url)
            offer_pks = seo_page.articles.filter(status__in=['I', 'U']) \
                .values_list('offer__pk', flat=True)
            queryset = Offers.objects.filter(pk__in=offer_pks) \
                .select_related('offer_products',
                                'offer_services',
                                'offer_solder') \
                .prefetch_related('offer_categories', 'for_whom', 'made_in_label',
                                  'offer_delivery')
            categories_query = self.get_filter_by_categories(queryset)
            colors_query = self.get_filter_by_colors(queryset)
            sizes_query = self.get_filter_by_sizes(queryset)
            for_whom_query = self.get_filter_by_for_whom(queryset)
            solder_query = self.get_filter_by_solder(queryset)
            labels_query = self.get_filter_by_labels(queryset)
            maroc_query = self.get_filter_by_maroc(queryset)
            cities_query = self.get_filter_by_cities(queryset)
            services_query = self.get_filter_by_services(queryset)
            # final_query = categories_query.union(colors_query, sizes_query,
            # for_whom_query, solder_query, labels_query,
            # maroc_query, cities_query, services_query)
            final_query = (categories_query | colors_query | sizes_query | for_whom_query | solder_query |
                           labels_query | maroc_query | cities_query | services_query).distinct()

            if final_query:
                return final_query
            return queryset
        except DefaultSeoPage.DoesNotExist:
            return None

    def get_filter_by_services(self, queryset: QuerySet) -> QuerySet:
        categories: Union[str, None] = self.request.query_params.get('categories', None)
        if categories:
            service = categories.split(',')
            if 'Services' in service:
                return queryset.filter(offer_type='S')
        return Offers.objects.none()

    def get_filter_by_categories(self, queryset: QuerySet) -> QuerySet:
        categories: Union[str, None] = self.request.query_params.get('categories', None)
        if categories:
            return queryset.filter(offer_categories__name_category__in=categories.split(','))
        return Offers.objects.none()

    def get_filter_by_colors(self, queryset: QuerySet) -> QuerySet:
        colors: Union[str, None] = self.request.query_params.get('colors', None)
        if colors:
            return queryset.filter(offer_products__product_colors__code_color__in=colors.split(','))
        return Offers.objects.none()

    def get_filter_by_sizes(self, queryset: QuerySet) -> QuerySet:
        sizes: Union[str, None] = self.request.query_params.get('sizes', None)
        if sizes:
            return queryset.filter(offer_products__product_sizes__code_size__in=sizes.split(','))
        return Offers.objects.none()

    def get_filter_by_for_whom(self, queryset: QuerySet) -> QuerySet:
        for_whom: Union[str, None] = self.request.query_params.get('forWhom', None)
        if for_whom:
            return queryset.filter(for_whom__name_for_whom__in=for_whom.split(','))
        return Offers.objects.none()

    def get_filter_by_solder(self, queryset: QuerySet) -> QuerySet:
        solder: Union[bool, None] = self.request.query_params.get('solder', None)
        if solder:
            return queryset.filter(offer_solder__exact=True)
        return Offers.objects.none()

    def get_filter_by_labels(self, queryset: QuerySet) -> QuerySet:
        labels: Union[bool, None] = self.request.query_params.get('labels', None)
        if labels:
            return queryset.filter(creator_label__exact=True)
        return Offers.objects.none()

    def get_filter_by_maroc(self, queryset: QuerySet) -> QuerySet:
        maroc: Union[bool, None] = self.request.query_params.get('maroc', None)
        if maroc:
            return queryset.filter(made_in_label__name_fr='Maroc')
        return Offers.objects.none()

    def get_filter_by_cities(self, queryset: QuerySet) -> QuerySet:
        cities = self.request.query_params.get('cities', None)
        if cities:
            q_one: QuerySet = queryset.filter(offer_delivery__delivery_city__name_fr__in=cities.split(','),
                                              offer_delivery__all_cities=True)
            return q_one
        return Offers.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset is None:
            errors = {"error": ["Page not found."]}
            raise ValidationError(errors)
        filter_queryset: QuerySet = self.filter_queryset(queryset)
        page = self.paginate_queryset(filter_queryset)
        if page is not None:
            serializer = self.get_serializer(filter_queryset, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response(response.data)
