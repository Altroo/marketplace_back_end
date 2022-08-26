from collections import defaultdict
from django.core.exceptions import SuspiciousFileOperation, ObjectDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import IntegrityError
from django.db.models import Count, F
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from shop.models import TempShop
from offers.models import TempOffers, TempSolder, TempServices, TempDelivery, TempProducts, \
    AuthShop, Offers, Solder, Products, Services, Delivery, OfferTags, \
    Categories, Colors, Sizes, ForWhom, ServiceDays, OfferVue, OffersTotalVues
from offers.base.serializers import BaseShopOfferSerializer, \
    BaseShopDeliverySerializer, BaseOfferDetailsSerializer, \
    BaseOffersListSerializer, BaseShopOfferSolderSerializer, \
    BaseShopOfferSolderPutSerializer, BaseShopProductSerializer, \
    BaseShopServiceSerializer, BaseProductPutSerializer, \
    BaseServicePutSerializer, BaseOfferPutSerializer, \
    BaseShopOfferDuplicateSerializer, BaseOfferTagsSerializer, \
    BaseOffersVuesListSerializer, \
    BaseTempOfferssListSerializer, BaseTempShopOfferSolderSerializer, \
    BaseTempShopOfferSolderPutSerializer, BaseTempOfferDetailsSerializer, BaseTempShopDeliverySerializer, \
    BaseTempShopServiceSerializer, BaseTempShopProductSerializer, BaseTempShopOfferSerializer, \
    BaseTempServicePutSerializer, BaseTempProductPutSerializer, BaseTempOfferPutSerializer
from offers.base.filters import TagsFilterSet
from os import path, remove
from Qaryb_API.settings import API_URL
from offers.base.tasks import base_generate_offer_thumbnails, base_duplicate_offer_images, \
    base_duplicate_offervue_images
from offers.mixins import PaginationMixinBy5
from places.models import City
from offers.base.pagination import GetMyVuesPagination
from datetime import datetime


class ShopOfferViewV2(APIView):
    permission_classes = (permissions.AllowAny,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def get(request, *args, **kwargs):
        offer_pk = kwargs.get('offer_pk')
        user = request.user
        # Temp offers
        if user.is_anonymous:
            try:
                offer = TempOffers.objects \
                    .select_related('temp_offer_solder') \
                    .select_related('temp_offer_products') \
                    .select_related('temp_offer_services') \
                    .prefetch_related('temp_offer_delivery') \
                    .get(pk=offer_pk)
                offer_details_serializer = BaseTempOfferDetailsSerializer(offer)
                return Response(offer_details_serializer.data, status=status.HTTP_200_OK)
            except TempOffers.DoesNotExist:
                errors = {"error": ["Offer not found."]}
                raise ValidationError(errors)
        # Real offers
        else:
            try:
                offer = Offers.objects \
                    .select_related('offer_solder') \
                    .select_related('offer_products') \
                    .select_related('offer_services') \
                    .prefetch_related('offer_delivery') \
                    .get(pk=offer_pk)
                offer_details_serializer = BaseOfferDetailsSerializer(offer, context={'user': user})
                # Increase vue by one get or create
                month = datetime.now().month
                try:
                    offer_vues = OfferVue.objects.get(offer=offer_pk)
                    offer_vues.nbr_total_vue += 1
                    offer_vues.save()
                except OfferVue.DoesNotExist:
                    OfferVue.objects.create(offer=offer, title=offer.title, nbr_total_vue=1).save()
                    # Duplicate pictures for buyer avatar & seller avatar & offer thumbnail
                    base_duplicate_offervue_images.apply_async((offer_pk,), )
                    # base_duplicate_offervue_images(offer_pk)
                try:
                    offers_total_vues = OffersTotalVues.objects.get(auth_shop=offer.auth_shop, date=month)
                    offers_total_vues.nbr_total_vue += 1
                    offers_total_vues.save()
                except OffersTotalVues.DoesNotExist:
                    OffersTotalVues.objects.create(auth_shop=offer.auth_shop, date=month, nbr_total_vue=1).save()
                return Response(offer_details_serializer.data, status=status.HTTP_200_OK)
            except Offers.DoesNotExist:
                errors = {"error": ["Offer not found."]}
                raise ValidationError(errors)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        # Temp offers
        if user.is_anonymous:
            unique_id = request.data.get('unique_id')
            try:
                shop = TempShop.objects.get(unique_id=unique_id)
            except TempShop.DoesNotExist:
                errors = {"error": ["Offer not found."]}
                raise ValidationError(errors)
            offer_type = request.data.get('offer_type')
            title = request.data.get('title')
            description = request.data.get('description')
            price = request.data.get('price')
            offer_serializer = BaseTempShopOfferSerializer(data={
                'auth_shop': shop.pk,
                'offer_type': offer_type,
                'title': title,
                'picture_1': request.data.get('picture_1', None),
                'picture_2': request.data.get('picture_2', None),
                'picture_3': request.data.get('picture_3', None),
                'description': description,
                'price': price,
            })
            if offer_serializer.is_valid():
                product_valid = False
                product_serializer_errors = None
                service_serializer_errors = None
                offer = offer_serializer.save()
                offer_pk = offer.pk
                # Generate thumbnails
                base_generate_offer_thumbnails.apply_async((offer_pk, 'TempOffers'), )
                data = {
                    'pk': offer_pk,
                    'offer_type': offer_type,
                    'title': title,
                    'picture_1': offer.get_absolute_picture_1_img,
                    'picture_1_thumb': offer.get_absolute_picture_1_thumbnail,
                    'picture_2': offer.get_absolute_picture_2_img,
                    'picture_2_thumb': offer.get_absolute_picture_2_thumbnail,
                    'picture_3': offer.get_absolute_picture_3_img,
                    'picture_3_thumb': offer.get_absolute_picture_3_thumbnail,
                    'description': description,
                    'price': price
                }
                # Categories
                offer_categories = str(request.data.get('offer_categories')).split(',')
                offer_categories = Categories.objects.filter(code_category__in=offer_categories)
                offer_categories_list = []
                for category in offer_categories:
                    offer.offer_categories.add(category.pk)
                    # offer_categories_list.append(category.code_category)
                    offer_categories_list.append(
                        {
                            "pk": category.pk,
                            "code_category": category.code_category,
                            "name_category": category.name_category
                        }
                    )
                data['offer_categories'] = offer_categories_list
                # ForWhom
                for_whom = str(request.data.get('for_whom')).split(',')
                for_whom = ForWhom.objects.filter(code_for_whom__in=for_whom)
                offer_for_whom_list = []
                for for_who in for_whom:
                    offer.for_whom.add(for_who.pk)
                    # offer_for_whom_list.append(for_who.code_for_whom)
                    offer_for_whom_list.append(
                        {
                            "pk": for_who.pk,
                            "code_for_whom": for_who.code_for_whom,
                            "name_for_whom": for_who.name_for_whom
                        }
                    )
                data['for_whom'] = offer_for_whom_list
                # Offer Tags
                # if Tags not choosen don't add the key to response.
                if request.data.get('tags') is not None:
                    tags = str(request.data.get('tags')).split(',')
                    for tag in tags:
                        try:
                            OfferTags.objects.create(name_tag=tag)
                        except IntegrityError:
                            pass
                    tags = OfferTags.objects.filter(name_tag__in=tags)
                    tags_list = []
                    for tag in tags:
                        offer.tags.add(tag.pk)
                        # tags_list.append(tag.name_tag)
                        tags_list.append(
                            {
                                "pk": tag.pk,
                                "name_tag": tag.name_tag,
                            }
                        )
                    data['tags'] = tags_list
                else:
                    # Return empty tags
                    data['tags'] = []
                # IF OFFER TYPE == V (VENTE) ; S (SERVICE)
                if offer_type == 'V':
                    product_quantity = request.data.get('product_quantity')
                    product_price_by = request.data.get('product_price_by')
                    product_longitude = request.data.get('product_longitude')
                    product_latitude = request.data.get('product_latitude')
                    product_address = request.data.get('product_address')
                    product_serializer = BaseTempShopProductSerializer(data={
                        'offer': offer_pk,
                        'product_quantity': product_quantity,
                        'product_price_by': product_price_by,
                        'product_longitude': product_longitude,
                        'product_latitude': product_latitude,
                        'product_address': product_address,
                    })
                    if product_serializer.is_valid():
                        product_valid = True
                        product = product_serializer.save()
                        # Colors
                        colors = str(request.data.get('product_colors')).split(',')
                        colors = Colors.objects.filter(code_color__in=colors)
                        product_colors_list = []
                        for color in colors:
                            product.product_colors.add(color.pk)
                            # product_colors_list.append(color.code_color)
                            product_colors_list.append(
                                {
                                    "pk": color.pk,
                                    "code_color": color.code_color,
                                    "name_color": color.name_color
                                }
                            )
                        data['product_colors'] = product_colors_list
                        # Sizes
                        sizes = str(request.data.get('product_sizes')).split(',')
                        sizes = Sizes.objects.filter(code_size__in=sizes)
                        product_sizes_list = []
                        for size in sizes:
                            product.product_sizes.add(size.pk)
                            # product_sizes_list.append(size.code_size)
                            product_sizes_list.append(
                                {
                                    "pk": size.pk,
                                    "code_color": size.code_size,
                                    "name_color": size.name_size
                                }
                            )
                        data['product_sizes'] = product_sizes_list
                        # PRODUCT RETURN DATA
                        data['product_quantity'] = product_quantity
                        data['product_price_by'] = product_price_by
                        data['product_longitude'] = product_longitude
                        data['product_latitude'] = product_latitude
                        data['product_address'] = product_address
                    else:
                        product_serializer_errors = product_serializer.errors
                elif offer_type == 'S':
                    service_morning_hour_from = request.data.get('service_morning_hour_from')
                    service_morning_hour_to = request.data.get('service_morning_hour_to')
                    service_afternoon_hour_from = request.data.get('service_afternoon_hour_from')
                    service_afternoon_hour_to = request.data.get('service_afternoon_hour_to')
                    service_zone_by = request.data.get('service_zone_by')
                    service_price_by = request.data.get('service_price_by')
                    service_longitude = request.data.get('service_longitude')
                    service_latitude = request.data.get('service_latitude')
                    service_address = request.data.get('service_address')
                    service_km_radius = request.data.get('service_km_radius')
                    service_serializer = BaseTempShopServiceSerializer(data={
                        'offer': offer_pk,
                        'service_morning_hour_from': service_morning_hour_from,
                        'service_morning_hour_to': service_morning_hour_to,
                        'service_afternoon_hour_from': service_afternoon_hour_from,
                        'service_afternoon_hour_to': service_afternoon_hour_to,
                        'service_zone_by': service_zone_by,
                        'service_price_by': service_price_by,
                        'service_longitude': service_longitude,
                        'service_latitude': service_latitude,
                        'service_address': service_address,
                        'service_km_radius': service_km_radius,
                    })
                    if service_serializer.is_valid():
                        service = service_serializer.save()
                        # Availability Days
                        availability_days = str(request.data.get('service_availability_days')).split(',')
                        availability_days = ServiceDays.objects.filter(code_day__in=availability_days)
                        service_availability_days_list = []
                        for availability_day in availability_days:
                            service.service_availability_days.add(availability_day.pk)
                            # service_availability_days_list.append(availability_day.code_day)
                            service_availability_days_list.append(
                                {
                                    "pk": availability_day.pk,
                                    "code_day": availability_day.code_day,
                                    "name_day": availability_day.name_day
                                }
                            )
                        data['service_availability_days'] = service_availability_days_list
                        # SERVICE RETURN DATA
                        data['service_morning_hour_from'] = service.service_morning_hour_from
                        data['service_morning_hour_to'] = service.service_morning_hour_to
                        data['service_afternoon_hour_from'] = service.service_afternoon_hour_from
                        data['service_afternoon_hour_to'] = service.service_afternoon_hour_to
                        data['service_zone_by'] = service.service_zone_by
                        data['service_price_by'] = service.service_price_by
                        data['service_longitude'] = service.service_longitude
                        data['service_latitude'] = service.service_latitude
                        data['service_address'] = service.service_address
                        data['service_km_radius'] = service.service_km_radius
                        # For services
                        return Response(data=data, status=status.HTTP_200_OK)
                    else:
                        service_serializer_errors = service_serializer.errors

                if product_valid:
                    # Deliveries
                    delivery_price_1 = request.data.get('delivery_price_1', None)
                    delivery_days_1 = request.data.get('delivery_days_1', None)

                    delivery_price_2 = request.data.get('delivery_price_2', None)
                    delivery_days_2 = request.data.get('delivery_days_2', None)

                    delivery_price_3 = request.data.get('delivery_price_3', None)
                    delivery_days_3 = request.data.get('delivery_days_3', None)

                    # Delivery 1 cities
                    delivery_city_1 = request.data.get('delivery_city_1')
                    delivery_cities_1_pk = []
                    delivery_cities_1 = []
                    if delivery_city_1:
                        cities_str = str(delivery_city_1).split(',')
                        cities = []
                        for city in cities_str:
                            cities.append(int(city))

                        cities = City.objects.filter(pk__in=cities)
                        for city in cities:
                            # delivery_cities_1.append(city.name_fr)
                            delivery_cities_1.append(
                                {
                                    "pk": city.pk,
                                    "city": city.name_fr,
                                }
                            )
                            delivery_cities_1_pk.append(city.pk)

                    # Delivery 2 cities
                    delivery_city_2 = request.data.get('delivery_city_2')
                    delivery_cities_2_pk = []
                    delivery_cities_2 = []
                    if delivery_city_2:
                        cities_str = str(delivery_city_2).split(',')
                        cities = []
                        for city in cities_str:
                            cities.append(int(city))

                        cities = City.objects.filter(pk__in=cities)
                        for city in cities:
                            # delivery_cities_2.append(city.name_fr)
                            delivery_cities_2.append(
                                {
                                    "pk": city.pk,
                                    "city": city.name_fr,
                                }
                            )
                            delivery_cities_2_pk.append(city.pk)

                    # Delivery 3 cities
                    delivery_city_3 = request.data.get('delivery_city_3')
                    delivery_cities_3_pk = []
                    delivery_cities_3 = []
                    if delivery_city_3:
                        cities_str = str(delivery_city_3).split(',')
                        cities = []
                        for city in cities_str:
                            cities.append(int(city))

                        cities = City.objects.filter(pk__in=cities)
                        for city in cities:
                            # delivery_cities_3.append(city.name_fr)
                            delivery_cities_3.append(
                                {
                                    "pk": city.pk,
                                    "city": city.name_fr,
                                }
                            )
                            delivery_cities_3_pk.append(city.pk)
                    deliveries = []
                    city_1_check = False
                    city_2_check = False
                    city_3_check = False
                    if delivery_city_1:
                        city_1_check = True
                        deliveries.append(
                            {
                                'offer': offer_pk,
                                'pk': offer_pk,
                                'delivery_city': delivery_cities_1,
                                'delivery_price': float(delivery_price_1),
                                'delivery_days': int(delivery_days_1)
                            }
                        )
                    if delivery_city_2:
                        city_2_check = True
                        deliveries.append(
                            {
                                'offer': offer_pk,
                                'pk': offer_pk,
                                'delivery_city': delivery_cities_2,
                                'delivery_price': float(delivery_price_2),
                                'delivery_days': int(delivery_days_2)
                            }
                        )
                    if delivery_city_3:
                        city_3_check = True
                        deliveries.append(
                            {
                                'offer': offer_pk,
                                'pk': offer_pk,
                                'delivery_city': delivery_cities_3,
                                'delivery_price': float(delivery_price_3),
                                'delivery_days': int(delivery_days_3)
                            }
                        )
                    delivery_serializer = BaseTempShopDeliverySerializer(data=deliveries, many=True)
                    if delivery_serializer.is_valid():
                        deliveries_serializer = delivery_serializer.save()
                        for delivery in deliveries_serializer:
                            if city_1_check:
                                delivery.delivery_city.add(*delivery_cities_1_pk)
                                city_1_check = False
                            elif city_2_check:
                                delivery.delivery_city.add(*delivery_cities_2_pk)
                                city_2_check = False
                            elif city_3_check:
                                delivery.delivery_city.add(*delivery_cities_3_pk)
                                city_3_check = False
                        for i in deliveries:
                            del i['offer']
                        data['deliveries'] = deliveries
                        # For products
                        return Response(data=data, status=status.HTTP_200_OK)
                    else:
                        raise ValidationError(delivery_serializer.errors)
                else:
                    offer.delete()
                    if offer_type == 'V' and product_serializer_errors:
                        raise ValidationError(product_serializer_errors.errors)
                    if offer_type == 'S' and service_serializer_errors:
                        raise ValidationError(service_serializer_errors.errors)
            raise ValidationError(offer_serializer.errors)
        # Real offers
        else:
            try:
                auth_shop = AuthShop.objects.get(user=user)
            except AuthShop.DoesNotExist:
                errors = {"error": ["Shop not found."]}
                raise ValidationError(errors)
            offer_type = request.data.get('offer_type')
            title = request.data.get('title')
            description = request.data.get('description')
            price = request.data.get('price')
            if auth_shop.creator:
                creator_label = request.data.get('creator_label')
                made_in_label = request.data.get('made_in_label')
            else:
                creator_label = False
                made_in_label = None
            offer_serializer = BaseShopOfferSerializer(data={
                'auth_shop': auth_shop.pk,
                'offer_type': offer_type,
                # Categories
                'title': title,
                'picture_1': request.data.get('picture_1', None),
                'picture_2': request.data.get('picture_2', None),
                'picture_3': request.data.get('picture_3', None),
                'description': description,
                'creator_label': creator_label,
                'made_in_label': made_in_label,
                # For whom
                'price': price,
            })
            if offer_serializer.is_valid():
                product_valid = False
                product_serializer_errors = None
                service_serializer_errors = None
                offer = offer_serializer.save()
                offer_pk = offer.pk
                # Generate thumbnails
                base_generate_offer_thumbnails.apply_async((offer_pk, 'Offers'), )
                data = {
                    'pk': offer_pk,
                    'offer_type': offer_type,
                    'title': title,
                    'picture_1': offer.get_absolute_picture_1_img,
                    'picture_1_thumb': offer.get_absolute_picture_1_thumbnail,
                    'picture_2': offer.get_absolute_picture_2_img,
                    'picture_2_thumb': offer.get_absolute_picture_2_thumbnail,
                    'picture_3': offer.get_absolute_picture_3_img,
                    'picture_3_thumb': offer.get_absolute_picture_3_thumbnail,
                    'description': description,
                    'creator_label': creator_label,
                    'made_in_label': made_in_label,
                    'price': price
                }
                # Categories
                offer_categories = str(request.data.get('offer_categories')).split(',')
                offer_categories = Categories.objects.filter(code_category__in=offer_categories)
                offer_categories_list = []
                for category in offer_categories:
                    offer.offer_categories.add(category.pk)
                    # offer_categories_list.append(category.code_category)
                    offer_categories_list.append(
                        {
                            "pk": category.pk,
                            "code_category": category.code_category,
                            "name_category": category.name_category
                        }
                    )
                data['offer_categories'] = offer_categories_list
                # ForWhom
                for_whom = str(request.data.get('for_whom')).split(',')
                for_whom = ForWhom.objects.filter(code_for_whom__in=for_whom)
                offer_for_whom_list = []
                for for_who in for_whom:
                    offer.for_whom.add(for_who.pk)
                    # offer_for_whom_list.append(for_who.code_for_whom)
                    offer_for_whom_list.append(
                        {
                            "pk": for_who.pk,
                            "code_for_whom": for_who.code_for_whom,
                            "name_for_whom": for_who.name_for_whom
                        }
                    )
                data['for_whom'] = offer_for_whom_list
                # Offer Tags
                # if Tags not choosen don't send the key.
                if request.data.get('tags') is not None:
                    tags = str(request.data.get('tags')).split(',')
                    for tag in tags:
                        try:
                            OfferTags.objects.create(name_tag=tag)
                        except IntegrityError:
                            pass
                    tags = OfferTags.objects.filter(name_tag__in=tags)
                    tags_list = []
                    for tag in tags:
                        offer.tags.add(tag.pk)
                        # tags_list.append(tag.name_tag)
                        tags_list.append(
                            {
                                "pk": tag.pk,
                                "name_tag": tag.name_tag,
                            }
                        )
                    data['tags'] = tags_list
                else:
                    # Return empty tags
                    data['tags'] = []
                # IF OFFER TYPE == V (VENTE) ; S (SERVICE)
                if offer_type == 'V':
                    product_quantity = request.data.get('product_quantity')
                    product_price_by = request.data.get('product_price_by')
                    product_longitude = request.data.get('product_longitude')
                    product_latitude = request.data.get('product_latitude')
                    product_address = request.data.get('product_address')
                    product_serializer = BaseShopProductSerializer(data={
                        'offer': offer_pk,
                        'product_quantity': product_quantity,
                        'product_price_by': product_price_by,
                        'product_longitude': product_longitude,
                        'product_latitude': product_latitude,
                        'product_address': product_address,
                    })
                    if product_serializer.is_valid():
                        product_valid = True
                        product = product_serializer.save()
                        # Colors
                        colors = str(request.data.get('product_colors')).split(',')
                        colors = Colors.objects.filter(code_color__in=colors)
                        product_colors_list = []
                        for color in colors:
                            product.product_colors.add(color.pk)
                            # product_colors_list.append(color.code_color)
                            product_colors_list.append(
                                {
                                    "pk": color.pk,
                                    "code_color": color.code_color,
                                    "name_color": color.name_color
                                }
                            )
                        data['product_colors'] = product_colors_list
                        # Sizes
                        sizes = str(request.data.get('product_sizes')).split(',')
                        sizes = Sizes.objects.filter(code_size__in=sizes)
                        product_sizes_list = []
                        for size in sizes:
                            product.product_sizes.add(size.pk)
                            # product_sizes_list.append(size.code_size)
                            product_sizes_list.append(
                                {
                                    "pk": size.pk,
                                    "code_color": size.code_size,
                                    "name_color": size.name_size
                                }
                            )
                        data['product_sizes'] = product_sizes_list
                        # PRODUCT RETURN DATA
                        data['product_quantity'] = product_quantity
                        data['product_price_by'] = product_price_by
                        data['product_longitude'] = product_longitude
                        data['product_latitude'] = product_latitude
                        data['product_address'] = product_address
                    else:
                        product_serializer_errors = product_serializer.errors
                elif offer_type == 'S':
                    service_morning_hour_from = request.data.get('service_morning_hour_from')
                    service_morning_hour_to = request.data.get('service_morning_hour_to')
                    service_afternoon_hour_from = request.data.get('service_afternoon_hour_from')
                    service_afternoon_hour_to = request.data.get('service_afternoon_hour_to')
                    service_zone_by = request.data.get('service_zone_by')
                    service_price_by = request.data.get('service_price_by')
                    service_longitude = request.data.get('service_longitude')
                    service_latitude = request.data.get('service_latitude')
                    service_address = request.data.get('service_address')
                    service_km_radius = request.data.get('service_km_radius')
                    service_serializer = BaseShopServiceSerializer(data={
                        'offer': offer_pk,
                        'service_morning_hour_from': service_morning_hour_from,
                        'service_morning_hour_to': service_morning_hour_to,
                        'service_afternoon_hour_from': service_afternoon_hour_from,
                        'service_afternoon_hour_to': service_afternoon_hour_to,
                        'service_zone_by': service_zone_by,
                        'service_price_by': service_price_by,
                        'service_longitude': service_longitude,
                        'service_latitude': service_latitude,
                        'service_address': service_address,
                        'service_km_radius': service_km_radius,
                    })
                    if service_serializer.is_valid():
                        service = service_serializer.save()
                        # Availability Days
                        availability_days = str(request.data.get('service_availability_days')).split(',')
                        availability_days = ServiceDays.objects.filter(code_day__in=availability_days)
                        service_availability_days_list = []
                        for availability_day in availability_days:
                            service.service_availability_days.add(availability_day.pk)
                            # service_availability_days_list.append(availability_day.code_day)
                            service_availability_days_list.append(
                                {
                                    "pk": availability_day.pk,
                                    "code_day": availability_day.code_day,
                                    "name_day": availability_day.name_day
                                }
                            )
                        data['service_availability_days'] = service_availability_days_list
                        # SERVICE RETURN DATA
                        data['service_morning_hour_from'] = service.service_morning_hour_from
                        data['service_morning_hour_to'] = service.service_morning_hour_to
                        data['service_afternoon_hour_from'] = service.service_afternoon_hour_from
                        data['service_afternoon_hour_to'] = service.service_afternoon_hour_to
                        data['service_zone_by'] = service.service_zone_by
                        data['service_price_by'] = service.service_price_by
                        data['service_longitude'] = service.service_longitude
                        data['service_latitude'] = service.service_latitude
                        data['service_address'] = service.service_address
                        data['service_km_radius'] = service.service_km_radius
                        # For services
                        return Response(data=data, status=status.HTTP_200_OK)
                    else:
                        service_serializer_errors = service_serializer.errors

                if product_valid:
                    # Deliveries
                    delivery_price_1 = request.data.get('delivery_price_1', None)
                    delivery_days_1 = request.data.get('delivery_days_1', None)

                    delivery_price_2 = request.data.get('delivery_price_2', None)
                    delivery_days_2 = request.data.get('delivery_days_2', None)

                    delivery_price_3 = request.data.get('delivery_price_3', None)
                    delivery_days_3 = request.data.get('delivery_days_3', None)

                    # Delivery 1 cities
                    delivery_city_1 = request.data.get('delivery_city_1')
                    delivery_cities_1_pk = []
                    delivery_cities_1 = []
                    if delivery_city_1:
                        cities_str = str(delivery_city_1).split(',')
                        cities = []
                        for city in cities_str:
                            cities.append(int(city))

                        cities = City.objects.filter(pk__in=cities)
                        for city in cities:
                            # delivery_cities_1.append(city.name_fr)
                            delivery_cities_1.append(
                                {
                                    "pk": city.pk,
                                    "city": city.name_fr,
                                }
                            )
                            delivery_cities_1_pk.append(city.pk)

                    # Delivery 2 cities
                    delivery_city_2 = request.data.get('delivery_city_2')
                    delivery_cities_2_pk = []
                    delivery_cities_2 = []
                    if delivery_city_2:
                        cities_str = str(delivery_city_2).split(',')
                        cities = []
                        for city in cities_str:
                            cities.append(int(city))

                        cities = City.objects.filter(pk__in=cities)
                        for city in cities:
                            # delivery_cities_2.append(city.name_fr)
                            delivery_cities_2.append(
                                {
                                    "pk": city.pk,
                                    "city": city.name_fr,
                                }
                            )
                            delivery_cities_2_pk.append(city.pk)

                    # Delivery 3 cities
                    delivery_city_3 = request.data.get('delivery_city_3')
                    delivery_cities_3_pk = []
                    delivery_cities_3 = []
                    if delivery_city_3:
                        cities_str = str(delivery_city_3).split(',')
                        cities = []
                        for city in cities_str:
                            cities.append(int(city))

                        cities = City.objects.filter(pk__in=cities)
                        for city in cities:
                            # delivery_cities_3.append(city.name_fr)
                            delivery_cities_3.append(
                                {
                                    "pk": city.pk,
                                    "city": city.name_fr,
                                }
                            )
                            delivery_cities_3_pk.append(city.pk)
                    deliveries = []
                    city_1_check = False
                    city_2_check = False
                    city_3_check = False
                    if delivery_city_1:
                        city_1_check = True
                        deliveries.append(
                            {
                                'offer': offer_pk,
                                'pk': offer_pk,
                                'delivery_city': delivery_cities_1,
                                'delivery_price': float(delivery_price_1),
                                'delivery_days': int(delivery_days_1)
                            }
                        )
                    if delivery_city_2:
                        city_2_check = True
                        deliveries.append(
                            {
                                'offer': offer_pk,
                                'pk': offer_pk,
                                'delivery_city': delivery_cities_2,
                                'delivery_price': float(delivery_price_2),
                                'delivery_days': int(delivery_days_2)
                            }
                        )
                    if delivery_city_3:
                        city_3_check = True
                        deliveries.append(
                            {
                                'offer': offer_pk,
                                'pk': offer_pk,
                                'delivery_city': delivery_cities_3,
                                'delivery_price': float(delivery_price_3),
                                'delivery_days': int(delivery_days_3)
                            }
                        )
                    delivery_serializer = BaseShopDeliverySerializer(data=deliveries, many=True)
                    if delivery_serializer.is_valid():
                        deliveries_serializer = delivery_serializer.save()
                        for delivery in deliveries_serializer:
                            if city_1_check:
                                delivery.delivery_city.add(*delivery_cities_1_pk)
                                city_1_check = False
                            elif city_2_check:
                                delivery.delivery_city.add(*delivery_cities_2_pk)
                                city_2_check = False
                            elif city_3_check:
                                delivery.delivery_city.add(*delivery_cities_3_pk)
                                city_3_check = False
                        for i in deliveries:
                            del i['offer']
                        data['deliveries'] = deliveries
                        # For products
                        return Response(data=data, status=status.HTTP_200_OK)
                    else:
                        raise ValidationError(delivery_serializer.errors)
                else:
                    offer.delete()
                    if offer_type == 'V' and product_serializer_errors:
                        raise ValidationError(product_serializer_errors.errors)
                    if offer_type == 'S' and service_serializer_errors:
                        raise ValidationError(service_serializer_errors.errors)
            raise ValidationError(offer_serializer.errors)

    def put(self, request, *args, **kwargs):
        offer_pk = request.data.get('offer_pk')
        user = request.user
        if user.is_anonymous:
            try:
                offer = TempOffers.objects.get(pk=offer_pk)
                offer_pk = offer.pk
                picture_1 = request.data.get('picture_1', None)
                picture_2 = request.data.get('picture_2', None)
                picture_3 = request.data.get('picture_3', None)

                previous_images = list()
                previous_images.append(API_URL + offer.picture_1.url
                                       if offer.picture_1 else False)
                previous_images.append(API_URL + offer.picture_2.url
                                       if offer.picture_2 else False)
                previous_images.append(API_URL + offer.picture_3.url
                                       if offer.picture_3 else False)

                if isinstance(picture_1, InMemoryUploadedFile):
                    try:
                        picture_1_path = self.parent_file_dir + offer.picture_1.url
                        picture_1_thumb_path = self.parent_file_dir + offer.picture_1_thumbnail.url
                        remove(picture_1_path)
                        remove(picture_1_thumb_path)
                    except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                        pass
                    offer.picture_1 = None
                    offer.save()
                else:
                    # src
                    if picture_1 in previous_images:
                        try:
                            img_1_index = previous_images.index(picture_1)
                            if img_1_index == 0:
                                picture_1 = offer.picture_1
                            elif img_1_index == 1:
                                picture_1 = offer.picture_2
                            else:
                                picture_1 = offer.picture_3
                        # None wasn't sent
                        except ValueError:
                            picture_1 = None

                if isinstance(picture_2, InMemoryUploadedFile):
                    try:
                        picture_2_path = self.parent_file_dir + offer.picture_2.url
                        picture_2_thumb_path = self.parent_file_dir + offer.picture_2_thumbnail.url
                        remove(picture_2_path)
                        remove(picture_2_thumb_path)
                    except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                        pass
                    offer.picture_2 = None
                    offer.save()
                else:
                    # src
                    if picture_2 in previous_images:
                        try:
                            img_2_index = previous_images.index(picture_2)
                            if img_2_index == 0:
                                picture_2 = offer.picture_1
                            elif img_2_index == 1:
                                picture_2 = offer.picture_2
                            else:
                                picture_2 = offer.picture_3
                        # None wasn't sent
                        except ValueError:
                            picture_2 = None

                if isinstance(picture_3, InMemoryUploadedFile):
                    try:
                        picture_3_path = self.parent_file_dir + offer.picture_3.url
                        picture_3_thumb_path = self.parent_file_dir + offer.picture_3_thumbnail.url
                        remove(picture_3_path)
                        remove(picture_3_thumb_path)
                    except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                        pass
                    offer.picture_3 = None
                    offer.save()
                else:
                    # src
                    if picture_3 in previous_images:
                        try:
                            img_3_index = previous_images.index(picture_3)
                            if img_3_index == 0:
                                picture_3 = offer.picture_1
                            elif img_3_index == 1:
                                picture_3 = offer.picture_2
                            else:
                                picture_3 = offer.picture_3
                        # None wasn't sent
                        except ValueError:
                            picture_3 = None

                title = request.data.get('title', '')
                description = request.data.get('description', '')
                price = request.data.get('price', '')
                # Temp product PUT serializer
                offer_serializer = BaseTempOfferPutSerializer(data={
                    'title': title,
                    'picture_1': picture_1,
                    'picture_2': picture_2,
                    'picture_3': picture_3,
                    'description': description,
                    'price': price,
                })
                if offer_serializer.is_valid():
                    offer_type = offer.offer_type
                    product_valid = False
                    service_valid = False
                    product_serializer_errors = None
                    service_serializer_errors = None
                    product_serializer = None
                    service_serializer = None
                    # Generate thumbnails
                    base_generate_offer_thumbnails.apply_async((offer_pk, 'TempOffers'), )
                    if offer.offer_type == 'V':
                        product_quantity = request.data.get('product_quantity', '')
                        product_price_by = request.data.get('product_price_by', '')
                        product_longitude = request.data.get('product_longitude', '')
                        product_latitude = request.data.get('product_latitude', '')
                        product_address = request.data.get('product_address', '')
                        product_serializer = BaseTempProductPutSerializer(data={
                            'product_quantity': product_quantity,
                            'product_price_by': product_price_by,
                            'product_longitude': product_longitude,
                            'product_latitude': product_latitude,
                            'product_address': product_address,
                        })
                        if product_serializer.is_valid():
                            product_valid = True
                        else:
                            product_serializer_errors = product_serializer.errors
                    elif offer.offer_type == 'S':
                        service_morning_hour_from = request.data.get('service_morning_hour_from', '')
                        service_morning_hour_to = request.data.get('service_morning_hour_to', '')
                        service_afternoon_hour_from = request.data.get('service_afternoon_hour_from', '')
                        service_afternoon_hour_to = request.data.get('service_afternoon_hour_to', '')
                        service_zone_by = request.data.get('service_zone_by', '')
                        service_price_by = request.data.get('service_price_by', '')
                        service_longitude = request.data.get('service_longitude', '')
                        service_latitude = request.data.get('service_latitude', '')
                        service_address = request.data.get('service_address', '')
                        service_serializer = BaseTempServicePutSerializer(data={
                            'service_morning_hour_from': service_morning_hour_from,
                            'service_morning_hour_to': service_morning_hour_to,
                            'service_afternoon_hour_from': service_afternoon_hour_from,
                            'service_afternoon_hour_to': service_afternoon_hour_to,
                            'service_zone_by': service_zone_by,
                            'service_price_by': service_price_by,
                            'service_longitude': service_longitude,
                            'service_latitude': service_latitude,
                            'service_address': service_address,
                        })
                        if service_serializer.is_valid():
                            service_valid = True
                        else:
                            service_serializer_errors = service_serializer.errors
                    if product_valid or service_valid:
                        # UPDATE OFFER TABLE
                        updated_offer = offer_serializer.update(offer, offer_serializer.validated_data)
                        data = {
                            'pk': updated_offer.pk,
                            'offer_type': updated_offer.offer_type,
                            'title': updated_offer.title,
                            'picture_1': updated_offer.get_absolute_picture_1_img,
                            'picture_1_thumb': updated_offer.get_absolute_picture_1_thumbnail,
                            'picture_2': updated_offer.get_absolute_picture_2_img,
                            'picture_2_thumb': updated_offer.get_absolute_picture_2_thumbnail,
                            'picture_3': updated_offer.get_absolute_picture_3_img,
                            'picture_3_thumb': updated_offer.get_absolute_picture_3_thumbnail,
                            'description': updated_offer.description,
                            'price': updated_offer.price
                        }
                        # UPDATE CATEGORIES
                        offer.offer_categories.clear()
                        offer_categories = str(request.data.get('offer_categories')).split(',')
                        new_categories = Categories.objects.filter(code_category__in=offer_categories)
                        offer_categories_list = []
                        for category in new_categories:
                            offer.offer_categories.add(category.pk)
                            # offer_categories_list.append(category.code_category)
                            offer_categories_list.append(
                                {
                                    "pk": category.pk,
                                    "code_category": category.code_category,
                                    "name_category": category.name_category
                                }
                            )
                        data['offer_categories'] = offer_categories_list
                        # UPDATE FOR WHOM
                        offer.for_whom.clear()
                        offer_for_whom = str(request.data.get('for_whom')).split(',')
                        new_for_whom = ForWhom.objects.filter(code_for_whom__in=offer_for_whom)
                        offer_for_whom_list = []
                        for for_who in new_for_whom:
                            offer.for_whom.add(for_who.pk)
                            # offer_for_whom_list.append(for_who.code_for_whom)
                            offer_for_whom_list.append(
                                {
                                    "pk": for_who.pk,
                                    "code_for_whom": for_who.code_for_whom,
                                    "name_for_whom": for_who.name_for_whom
                                }
                            )
                        data['for_whom'] = offer_for_whom_list
                        # UPDATE OFFER TAGS
                        offer.tags.clear()
                        # Offer Tags
                        tags = str(request.data.get('tags')).split(',')
                        for tag in tags:
                            try:
                                OfferTags.objects.create(name_tag=tag)
                            except IntegrityError:
                                pass
                        tags = OfferTags.objects.filter(name_tag__in=tags)
                        tags_list = []
                        for tag in tags:
                            offer.tags.add(tag.pk)
                            # tags_list.append(tag.name_tag)
                            tags_list.append(
                                {
                                    "pk": tag.pk,
                                    "name_tag": tag.name_tag,
                                }
                            )
                        data['tags'] = tags_list
                        if product_valid:
                            product = TempProducts.objects.get(offer=offer.pk)
                            # serializer referenced before assignment fixed by the product_valid = True
                            updated_product = product_serializer.update(product, product_serializer.validated_data)
                            # UPDATE COLORS
                            product.product_colors.clear()
                            colors = str(request.data.get('product_colors')).split(',')
                            new_colors = Colors.objects.filter(code_color__in=colors)
                            product_colors_list = []
                            for color in new_colors:
                                product.product_colors.add(color.pk)
                                # product_colors_list.append(color.code_color)
                                product_colors_list.append(
                                    {
                                        "pk": color.pk,
                                        "code_color": color.code_color,
                                        "name_color": color.name_color
                                    }
                                )
                            data['product_colors'] = product_colors_list
                            # UPDATE SIZES
                            product.product_sizes.clear()
                            sizes = str(request.data.get('product_sizes')).split(',')
                            new_sizes = Sizes.objects.filter(code_size__in=sizes)
                            product_sizes_list = []
                            for size in new_sizes:
                                product.product_sizes.add(size.pk)
                                # product_sizes_list.append(size.code_size)
                                product_sizes_list.append(
                                    {
                                        "pk": size.pk,
                                        "code_size": size.code_size,
                                        "name_size": size.name_size
                                    }
                                )
                            data['product_sizes'] = product_sizes_list
                            # PRODUCT RETURN DATA
                            data['product_quantity'] = updated_product.product_quantity
                            data['product_price_by'] = updated_product.product_price_by
                            data['product_longitude'] = updated_product.product_longitude
                            data['product_latitude'] = updated_product.product_latitude
                            data['product_address'] = updated_product.product_address
                            # UPDATE DELIVERIES
                            offer.temp_offer_delivery.all().delete()
                            delivery_price_1 = request.data.get('delivery_price_1', None)
                            delivery_days_1 = request.data.get('delivery_days_1', None)

                            delivery_price_2 = request.data.get('delivery_price_2', None)
                            delivery_days_2 = request.data.get('delivery_days_2', None)

                            delivery_price_3 = request.data.get('delivery_price_3', None)
                            delivery_days_3 = request.data.get('delivery_days_3', None)

                            # Delivery 1 cities
                            delivery_city_1 = request.data.get('delivery_city_1')
                            delivery_cities_1_pk = []
                            delivery_cities_1 = []
                            if delivery_city_1:
                                cities_str = str(delivery_city_1).split(',')
                                cities = []
                                for city in cities_str:
                                    cities.append(int(city))

                                cities = City.objects.filter(pk__in=cities)
                                for city in cities:
                                    # delivery_cities_1.append(city.name_fr)
                                    delivery_cities_1.append(
                                        {
                                            "pk": city.pk,
                                            "city": city.name_fr,
                                        }
                                    )
                                    # delivery_cities_1_pk.append(city.pk)

                            # Delivery 2 cities
                            delivery_city_2 = request.data.get('delivery_city_2')
                            delivery_cities_2_pk = []
                            delivery_cities_2 = []
                            if delivery_city_2:
                                cities_str = str(delivery_city_2).split(',')
                                cities = []
                                for city in cities_str:
                                    cities.append(int(city))

                                cities = City.objects.filter(pk__in=cities)
                                for city in cities:
                                    # delivery_cities_2.append(city.name_fr)
                                    delivery_cities_2.append(
                                        {
                                            "pk": city.pk,
                                            "city": city.name_fr,
                                        }
                                    )
                                    delivery_cities_2_pk.append(city.pk)

                            # Delivery 3 cities
                            delivery_city_3 = request.data.get('delivery_city_3')
                            delivery_cities_3_pk = []
                            delivery_cities_3 = []
                            if delivery_city_3:
                                cities_str = str(delivery_city_3).split(',')
                                cities = []
                                for city in cities_str:
                                    cities.append(int(city))

                                cities = City.objects.filter(pk__in=cities)
                                for city in cities:
                                    # delivery_cities_3.append(city.name_fr)
                                    delivery_cities_3.append(
                                        {
                                            "pk": city.pk,
                                            "city": city.name_fr,
                                        }
                                    )
                                    delivery_cities_3_pk.append(city.pk)

                            deliveries = []
                            city_1_check = False
                            city_2_check = False
                            city_3_check = False

                            if delivery_city_1:
                                city_1_check = True
                                deliveries.append(
                                    {
                                        'offer': offer_pk,
                                        'pk': offer_pk,
                                        'delivery_city': delivery_city_1,
                                        'delivery_price': float(delivery_price_1),
                                        'delivery_days': int(delivery_days_1)
                                    }
                                )
                            if delivery_city_2:
                                city_2_check = True
                                deliveries.append(
                                    {
                                        'offer': offer_pk,
                                        'pk': offer_pk,
                                        'delivery_city': delivery_city_2,
                                        'delivery_price': float(delivery_price_2),
                                        'delivery_days': int(delivery_days_2)
                                    }
                                )
                            if delivery_city_3:
                                city_3_check = True
                                deliveries.append(
                                    {
                                        'offer': offer_pk,
                                        'pk': offer_pk,
                                        'delivery_city': delivery_city_3,
                                        'delivery_price': float(delivery_price_3),
                                        'delivery_days': int(delivery_days_3)
                                    }
                                )

                            # Save edited deliveries
                            delivery_serializer = BaseTempShopDeliverySerializer(data=deliveries, many=True)
                            if delivery_serializer.is_valid():
                                # Delete old deliveries cities
                                TempDelivery.objects.filter(offer__pk=offer_pk).delete()
                                # Add new deliveries
                                deliveries_serializer = delivery_serializer.save()
                                for delivery in deliveries_serializer:
                                    if city_1_check:
                                        delivery.delivery_city.add(*delivery_cities_1_pk)
                                        city_1_check = False
                                    elif city_2_check:
                                        delivery.delivery_city.add(*delivery_cities_2_pk)
                                        city_2_check = False
                                    elif city_3_check:
                                        delivery.delivery_city.add(*delivery_cities_3_pk)
                                        city_3_check = False
                                for i in deliveries:
                                    del i['offer']
                                data['deliveries'] = deliveries
                                return Response(data, status=status.HTTP_200_OK)
                            else:
                                raise ValidationError(delivery_serializer.errors)
                        if service_valid:
                            service = TempServices.objects.get(offer=offer.pk)
                            # serializer referenced before assignment fixed by the service_valid = True
                            updated_service = service_serializer.update(service, service_serializer.validated_data)
                            # UPDATE AVAILABILITY DAYS
                            service.service_availability_days.clear()
                            availability_days = str(request.data.get('service_availability_days')).split(',')
                            new_availability_days = ServiceDays.objects.filter(code_day__in=availability_days)
                            service_availability_days_list = []
                            for availability_day in new_availability_days:
                                service.service_availability_days.add(availability_day.pk)
                                # service_availability_days_list.append(availability_day.code_day)
                                service_availability_days_list.append(
                                    {
                                        "pk": availability_day.pk,
                                        "code_day": availability_day.code_size,
                                        "name_day": availability_day.name_size
                                    }
                                )
                            data['service_availability_days'] = service_availability_days_list
                            # SERVICE RETURN DATA
                            data['service_morning_hour_from'] = updated_service.service_morning_hour_from
                            data['service_morning_hour_to'] = updated_service.service_morning_hour_to
                            data['service_afternoon_hour_from'] = updated_service.service_afternoon_hour_from
                            data['service_afternoon_hour_to'] = updated_service.service_afternoon_hour_to
                            data['service_zone_by'] = updated_service.service_zone_by
                            data['service_price_by'] = updated_service.service_price_by
                            data['service_longitude'] = updated_service.service_longitude
                            data['service_latitude'] = updated_service.service_latitude
                            data['service_address'] = updated_service.service_address
                            data['service_km_radius'] = updated_service.service_km_radius
                            return Response(data, status=status.HTTP_200_OK)
                    else:
                        if offer_type == 'V' and product_serializer_errors:
                            raise ValidationError(product_serializer_errors)
                        if offer_type == 'S' and service_serializer_errors:
                            raise ValidationError(service_serializer_errors)
                raise ValidationError(offer_serializer.errors)
            except TempOffers.DoesNotExist:
                errors = {"error": ["Offer not found."]}
                raise ValidationError(errors)
        # Real offers
        else:
            try:
                offer = Offers.objects.get(pk=offer_pk)
                offer_pk = offer.pk
                picture_1 = request.data.get('picture_1', None)
                picture_2 = request.data.get('picture_2', None)
                picture_3 = request.data.get('picture_3', None)

                previous_images = list()
                previous_images.append(API_URL + offer.picture_1.url
                                       if offer.picture_1 else False)
                previous_images.append(API_URL + offer.picture_2.url
                                       if offer.picture_2 else False)
                previous_images.append(API_URL + offer.picture_3.url
                                       if offer.picture_3 else False)

                if isinstance(picture_1, InMemoryUploadedFile):
                    try:
                        picture_1_path = self.parent_file_dir + offer.picture_1.url
                        picture_1_thumb_path = self.parent_file_dir + offer.picture_1_thumbnail.url
                        remove(picture_1_path)
                        remove(picture_1_thumb_path)
                    except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                        pass
                    offer.picture_1 = None
                    offer.save()
                else:

                    if picture_1 in previous_images:
                        try:
                            img_1_index = previous_images.index(picture_1)
                            if img_1_index == 0:
                                picture_1 = offer.picture_1
                            elif img_1_index == 1:
                                picture_1 = offer.picture_2
                            else:
                                picture_1 = offer.picture_3
                        # None wasn't sent
                        except ValueError:
                            picture_1 = None

                if isinstance(picture_2, InMemoryUploadedFile):
                    try:
                        picture_2_path = self.parent_file_dir + offer.picture_2.url
                        picture_2_thumb_path = self.parent_file_dir + offer.picture_2_thumbnail.url
                        remove(picture_2_path)
                        remove(picture_2_thumb_path)
                    except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                        pass
                    offer.picture_2 = None
                    offer.save()
                else:
                    # src
                    if picture_2 in previous_images:
                        try:
                            img_2_index = previous_images.index(picture_2)
                            if img_2_index == 0:
                                picture_2 = offer.picture_1
                            elif img_2_index == 1:
                                picture_2 = offer.picture_2
                            else:
                                picture_2 = offer.picture_3
                        # None wasn't
                        except ValueError:
                            picture_2 = None

                if isinstance(picture_3, InMemoryUploadedFile):
                    try:
                        picture_3_path = self.parent_file_dir + offer.picture_3.url
                        picture_3_thumb_path = self.parent_file_dir + offer.picture_3_thumbnail.url
                        remove(picture_3_path)
                        remove(picture_3_thumb_path)
                    except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                        pass
                    offer.picture_3 = None
                    offer.save()
                else:
                    # src
                    if picture_3 in previous_images:
                        try:
                            img_3_index = previous_images.index(picture_3)
                            if img_3_index == 0:
                                picture_3 = offer.picture_1
                            elif img_3_index == 1:
                                picture_3 = offer.picture_2
                            else:
                                picture_3 = offer.picture_3
                        # None wasn't sent
                        except ValueError:
                            picture_3 = None

                title = request.data.get('title', '')
                description = request.data.get('description', '')
                price = request.data.get('price', '')
                if offer.auth_shop.creator:
                    creator_label = request.data.get('creator_label')
                    made_in_label = request.data.get('made_in_label')
                else:
                    creator_label = False
                    made_in_label = None
                # Product PUT serializer
                offer_serializer = BaseOfferPutSerializer(data={
                    'title': title,
                    'picture_1': picture_1,
                    'picture_2': picture_2,
                    'picture_3': picture_3,
                    'description': description,
                    'creator_label': creator_label,
                    'made_in_label': made_in_label,
                    'price': price,
                })
                if offer_serializer.is_valid():
                    offer_type = offer.offer_type
                    product_valid = False
                    service_valid = False
                    product_serializer_errors = None
                    service_serializer_errors = None
                    product_serializer = None
                    service_serializer = None
                    # Generate thumbnails
                    base_generate_offer_thumbnails.apply_async((offer_pk, 'Offers'), )
                    if offer.offer_type == 'V':
                        product_quantity = request.data.get('product_quantity', '')
                        product_price_by = request.data.get('product_price_by', '')
                        product_longitude = request.data.get('product_longitude', '')
                        product_latitude = request.data.get('product_latitude', '')
                        product_address = request.data.get('product_address', '')
                        product_serializer = BaseProductPutSerializer(data={
                            'product_quantity': product_quantity,
                            'product_price_by': product_price_by,
                            'product_longitude': product_longitude,
                            'product_latitude': product_latitude,
                            'product_address': product_address,
                        })
                        if product_serializer.is_valid():
                            product_valid = True
                        else:
                            product_serializer_errors = product_serializer.errors
                    elif offer.offer_type == 'S':
                        service_morning_hour_from = request.data.get('service_morning_hour_from', '')
                        service_morning_hour_to = request.data.get('service_morning_hour_to', '')
                        service_afternoon_hour_from = request.data.get('service_afternoon_hour_from', '')
                        service_afternoon_hour_to = request.data.get('service_afternoon_hour_to', '')
                        service_zone_by = request.data.get('service_zone_by', '')
                        service_price_by = request.data.get('service_price_by', '')
                        service_longitude = request.data.get('service_longitude', '')
                        service_latitude = request.data.get('service_latitude', '')
                        service_address = request.data.get('service_address', '')
                        service_serializer = BaseServicePutSerializer(data={
                            'service_morning_hour_from': service_morning_hour_from,
                            'service_morning_hour_to': service_morning_hour_to,
                            'service_afternoon_hour_from': service_afternoon_hour_from,
                            'service_afternoon_hour_to': service_afternoon_hour_to,
                            'service_zone_by': service_zone_by,
                            'service_price_by': service_price_by,
                            'service_longitude': service_longitude,
                            'service_latitude': service_latitude,
                            'service_address': service_address,
                        })
                        if service_serializer.is_valid():
                            service_valid = True
                        else:
                            service_serializer_errors = service_serializer.errors
                    if product_valid or service_valid:
                        # UPDATE OFFER TABLE
                        updated_offer = offer_serializer.update(offer, offer_serializer.validated_data)
                        data = {
                            'pk': updated_offer.pk,
                            'offer_type': updated_offer.offer_type,
                            'title': updated_offer.title,
                            'picture_1': updated_offer.get_absolute_picture_1_img,
                            'picture_1_thumb': updated_offer.get_absolute_picture_1_thumbnail,
                            'picture_2': updated_offer.get_absolute_picture_2_img,
                            'picture_2_thumb': updated_offer.get_absolute_picture_2_thumbnail,
                            'picture_3': updated_offer.get_absolute_picture_3_img,
                            'picture_3_thumb': updated_offer.get_absolute_picture_3_thumbnail,
                            'description': updated_offer.description,
                            'price': updated_offer.price
                        }
                        # UPDATE CATEGORIES
                        offer.offer_categories.clear()
                        offer_categories = str(request.data.get('offer_categories')).split(',')
                        new_categories = Categories.objects.filter(code_category__in=offer_categories)
                        offer_categories_list = []
                        for category in new_categories:
                            offer.offer_categories.add(category.pk)
                            # offer_categories_list.append(category.code_category)
                            offer_categories_list.append(
                                {
                                    "pk": category.pk,
                                    "code_category": category.code_category,
                                    "name_category": category.name_category
                                }
                            )
                        data['offer_categories'] = offer_categories_list
                        # UPDATE FOR WHOM
                        offer.for_whom.clear()
                        offer_for_whom = str(request.data.get('for_whom')).split(',')
                        new_for_whom = ForWhom.objects.filter(code_for_whom__in=offer_for_whom)
                        offer_for_whom_list = []
                        for for_who in new_for_whom:
                            offer.for_whom.add(for_who.pk)
                            # offer_for_whom_list.append(for_who.code_for_whom)
                            offer_for_whom_list.append(
                                {
                                    "pk": for_who.pk,
                                    "code_for_whom": for_who.code_for_whom,
                                    "name_for_whom": for_who.name_for_whom
                                }
                            )
                        data['for_whom'] = offer_for_whom_list
                        # UPDATE OFFER TAGS
                        offer.tags.clear()
                        # Offer Tags
                        tags = str(request.data.get('tags')).split(',')
                        for tag in tags:
                            try:
                                OfferTags.objects.create(name_tag=tag)
                            except IntegrityError:
                                pass
                        tags = OfferTags.objects.filter(name_tag__in=tags)
                        tags_list = []
                        for tag in tags:
                            offer.tags.add(tag.pk)
                            # tags_list.append(tag.name_tag)
                            tags_list.append(
                                {
                                    "pk": tag.pk,
                                    "name_tag": tag.name_tag,
                                }
                            )
                        data['tags'] = tags_list
                        if product_valid:
                            product = Products.objects.get(offer=offer.pk)
                            # serializer referenced before assignment fixed by the product_valid = True
                            updated_product = product_serializer.update(product, product_serializer.validated_data)
                            # UPDATE COLORS
                            product.product_colors.clear()
                            colors = str(request.data.get('product_colors')).split(',')
                            new_colors = Colors.objects.filter(code_color__in=colors)
                            product_colors_list = []
                            for color in new_colors:
                                product.product_colors.add(color.pk)
                                # product_colors_list.append(color.code_color)
                                product_colors_list.append(
                                    {
                                        "pk": color.pk,
                                        "code_color": color.code_color,
                                        "name_color": color.name_color
                                    }
                                )
                            data['product_colors'] = product_colors_list
                            # UPDATE SIZES
                            product.product_sizes.clear()
                            sizes = str(request.data.get('product_sizes')).split(',')
                            new_sizes = Sizes.objects.filter(code_size__in=sizes)
                            product_sizes_list = []
                            for size in new_sizes:
                                product.product_sizes.add(size.pk)
                                # product_sizes_list.append(size.code_size)
                                product_sizes_list.append(
                                    {
                                        "pk": size.pk,
                                        "code_size": size.code_size,
                                        "name_size": size.name_size
                                    }
                                )
                            data['product_sizes'] = product_sizes_list
                            # PRODUCT RETURN DATA
                            data['product_quantity'] = updated_product.product_quantity
                            data['product_price_by'] = updated_product.product_price_by
                            data['product_longitude'] = updated_product.product_longitude
                            data['product_latitude'] = updated_product.product_latitude
                            data['product_address'] = updated_product.product_address
                            # UPDATE DELIVERIES
                            offer.offer_delivery.all().delete()
                            delivery_price_1 = request.data.get('delivery_price_1', None)
                            delivery_days_1 = request.data.get('delivery_days_1', None)

                            delivery_price_2 = request.data.get('delivery_price_2', None)
                            delivery_days_2 = request.data.get('delivery_days_2', None)

                            delivery_price_3 = request.data.get('delivery_price_3', None)
                            delivery_days_3 = request.data.get('delivery_days_3', None)

                            # Delivery 1 cities
                            delivery_city_1 = request.data.get('delivery_city_1')
                            delivery_cities_1_pk = []
                            delivery_cities_1 = []
                            if delivery_city_1:
                                cities_str = str(delivery_city_1).split(',')
                                cities = []
                                for city in cities_str:
                                    cities.append(int(city))

                                cities = City.objects.filter(pk__in=cities)
                                for city in cities:
                                    # delivery_cities_1.append(city.name_fr)
                                    delivery_cities_1.append(
                                        {
                                            "pk": city.pk,
                                            "city": city.name_fr,
                                        }
                                    )
                                    delivery_cities_1_pk.append(city.pk)

                            # Delivery 2 cities
                            delivery_city_2 = request.data.get('delivery_city_2')
                            delivery_cities_2_pk = []
                            delivery_cities_2 = []
                            if delivery_city_2:
                                cities_str = str(delivery_city_2).split(',')
                                cities = []
                                for city in cities_str:
                                    cities.append(int(city))

                                cities = City.objects.filter(pk__in=cities)
                                for city in cities:
                                    # delivery_cities_2.append(city.name_fr)
                                    delivery_cities_2.append(
                                        {
                                            "pk": city.pk,
                                            "city": city.name_fr,
                                        }
                                    )
                                    delivery_cities_2_pk.append(city.pk)

                            # Delivery 3 cities
                            delivery_city_3 = request.data.get('delivery_city_3')
                            delivery_cities_3_pk = []
                            delivery_cities_3 = []
                            if delivery_city_3:
                                cities_str = str(delivery_city_3).split(',')
                                cities = []
                                for city in cities_str:
                                    cities.append(int(city))

                                cities = City.objects.filter(pk__in=cities)
                                for city in cities:
                                    # delivery_cities_3.append(city.name_fr)
                                    delivery_cities_3.append(
                                        {
                                            "pk": city.pk,
                                            "city": city.name_fr,
                                        }
                                    )
                                    delivery_cities_3_pk.append(city.pk)

                            deliveries = []
                            city_1_check = False
                            city_2_check = False
                            city_3_check = False
                            if delivery_city_1:
                                city_1_check = True
                                deliveries.append(
                                    {
                                        'offer': offer_pk,
                                        'pk': offer_pk,
                                        'delivery_city': delivery_cities_1,
                                        'delivery_price': float(delivery_price_1),
                                        'delivery_days': int(delivery_days_1)
                                    }
                                )
                            if delivery_city_2:
                                city_2_check = True
                                deliveries.append(
                                    {
                                        'offer': offer_pk,
                                        'pk': offer_pk,
                                        'delivery_city': delivery_cities_2,
                                        'delivery_price': float(delivery_price_2),
                                        'delivery_days': int(delivery_days_2)
                                    }
                                )
                            if delivery_city_3:
                                city_3_check = True
                                deliveries.append(
                                    {
                                        'offer': offer_pk,
                                        'pk': offer_pk,
                                        'delivery_city': delivery_cities_3,
                                        'delivery_price': float(delivery_price_3),
                                        'delivery_days': int(delivery_days_3)
                                    }
                                )

                            # Save edited deliveries
                            delivery_serializer = BaseShopDeliverySerializer(data=deliveries, many=True)
                            if delivery_serializer.is_valid():
                                # Delete old deliveries cities
                                Delivery.objects.filter(offer__pk=offer_pk).delete()
                                # Add new deliveries
                                deliveries_serializer = delivery_serializer.save()
                                for delivery in deliveries_serializer:
                                    if city_1_check:
                                        delivery.delivery_city.add(*delivery_cities_1_pk)
                                        city_1_check = False
                                    elif city_2_check:
                                        delivery.delivery_city.add(*delivery_cities_2_pk)
                                        city_2_check = False
                                    elif city_3_check:
                                        delivery.delivery_city.add(*delivery_cities_3_pk)
                                        city_3_check = False
                                for i in deliveries:
                                    del i['offer']
                                data['deliveries'] = deliveries
                                return Response(data, status=status.HTTP_200_OK)
                            else:
                                raise ValidationError(delivery_serializer.errors)
                        if service_valid:
                            service = Services.objects.get(offer=offer.pk)
                            # serializer referenced before assignment fixed by the service_valid = True
                            updated_service = service_serializer.update(service, service_serializer.validated_data)
                            # UPDATE AVAILABILITY DAYS
                            service.service_availability_days.clear()
                            availability_days = str(request.data.get('service_availability_days')).split(',')
                            new_availability_days = ServiceDays.objects.filter(code_day__in=availability_days)
                            service_availability_days_list = []
                            for availability_day in new_availability_days:
                                service.service_availability_days.add(availability_day.pk)
                                # service_availability_days_list.append(availability_day.code_day)
                                service_availability_days_list.append(
                                    {
                                        "pk": availability_day.pk,
                                        "code_day": availability_day.code_size,
                                        "name_day": availability_day.name_size
                                    }
                                )
                            data['service_availability_days'] = service_availability_days_list
                            # SERVICE RETURN DATA
                            data['service_morning_hour_from'] = updated_service.service_morning_hour_from
                            data['service_morning_hour_to'] = updated_service.service_morning_hour_to
                            data['service_afternoon_hour_from'] = updated_service.service_afternoon_hour_from
                            data['service_afternoon_hour_to'] = updated_service.service_afternoon_hour_to
                            data['service_zone_by'] = updated_service.service_zone_by
                            data['service_price_by'] = updated_service.service_price_by
                            data['service_longitude'] = updated_service.service_longitude
                            data['service_latitude'] = updated_service.service_latitude
                            data['service_address'] = updated_service.service_address
                            data['service_km_radius'] = updated_service.service_km_radius
                            return Response(data, status=status.HTTP_200_OK)
                    else:
                        if offer_type == 'V' and product_serializer_errors:
                            raise ValidationError(product_serializer_errors)
                        if offer_type == 'S' and service_serializer_errors:
                            raise ValidationError(service_serializer_errors)
                raise ValidationError(offer_serializer.errors)
            except Offers.DoesNotExist:
                errors = {"error": ["Offer not found."]}
                raise ValidationError(errors)

    @staticmethod
    def delete(request, *args, **kwargs):
        offer_pk = kwargs.get('offer_pk')
        user = request.user
        # Teamp offers
        if user.is_anonymous:
            unique_id = kwargs.get('unique_id')
            try:
                offer = TempOffers.objects.get(pk=offer_pk)
                if offer.auth_shop.unique_id != unique_id:
                    errors = {"error": ["Offer not yours to delete."]}
                    raise ValidationError(errors)
                # Delete temp product images
                # Picture 1
                try:
                    picture_1 = offer.picture_1.path
                    remove(picture_1)
                except (FileNotFoundError, ValueError, AttributeError):
                    pass
                # Picture 1 thumbnail
                try:
                    picture_1_thumbnail = offer.picture_1_thumbnail.path
                    remove(picture_1_thumbnail)
                except (FileNotFoundError, ValueError, AttributeError):
                    pass
                # Picture 2
                try:
                    picture_2 = offer.picture_2.path
                    remove(picture_2)
                except (FileNotFoundError, ValueError, AttributeError):
                    pass
                # Picture 2 thumbnail
                try:
                    picture_2_thumbnail = offer.picture_2_thumbnail.path
                    remove(picture_2_thumbnail)
                except (FileNotFoundError, ValueError, AttributeError):
                    pass
                # Picture 3
                try:
                    picture_3 = offer.picture_3.path
                    remove(picture_3)
                except (FileNotFoundError, ValueError, AttributeError):
                    pass
                # Picture 3 thumbnail
                try:
                    picture_3_thumbnail = offer.picture_3_thumbnail.path
                    remove(picture_3_thumbnail)
                except (FileNotFoundError, ValueError, AttributeError):
                    pass
                offer.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except TempOffers.DoesNotExist:
                errors = {"error": ["Offer not found."]}
                raise ValidationError(errors)
        # Real offers
        else:
            try:
                shop = AuthShop.objects.get(user=user)
            except AuthShop.DoesNotExist:
                errors = {"error": ["Shop not found."]}
                raise ValidationError(errors)
            offers = Offers.objects.filter(auth_shop=shop)
            deleted = False
            for offer in offers:
                if offer.pk == offer_pk:
                    # Delete  product images
                    # Picture 1
                    try:
                        picture_1 = offer.picture_1.path
                        remove(picture_1)
                    except (FileNotFoundError, ValueError, AttributeError):
                        pass
                    # Picture 1 thumbnail
                    try:
                        picture_1_thumbnail = offer.picture_1_thumbnail.path
                        remove(picture_1_thumbnail)
                    except (FileNotFoundError, ValueError, AttributeError):
                        pass
                    # Picture 2
                    try:
                        picture_2 = offer.picture_2.path
                        remove(picture_2)
                    except (FileNotFoundError, ValueError, AttributeError):
                        pass
                    # Picture 2 thumbnail
                    try:
                        picture_2_thumbnail = offer.picture_2_thumbnail.path
                        remove(picture_2_thumbnail)
                    except (FileNotFoundError, ValueError, AttributeError):
                        pass
                    # Picture 3
                    try:
                        picture_3 = offer.picture_3.path
                        remove(picture_3)
                    except (FileNotFoundError, ValueError, AttributeError):
                        pass
                    # Picture 3 thumbnail
                    try:
                        picture_3_thumbnail = offer.picture_3_thumbnail.path
                        remove(picture_3_thumbnail)
                    except (FileNotFoundError, ValueError, AttributeError):
                        pass
                    offer.delete()
                    deleted = True
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                errors = {"error": ["Offer not yours to delete."]}
                raise ValidationError(errors)


class GetMyShopOffersListView(APIView, PaginationMixinBy5):
    permission_classes = (permissions.AllowAny,)

    # filter_class = BaseOffersListFilter

    def get(self, request, *args, **kwargs):
        user = request.user
        # Temp offers
        if user.is_anonymous:
            unique_id = kwargs.get('unique_id')
            try:
                auth_shop = TempShop.objects.get(unique_id=unique_id)
                offers = TempOffers.objects \
                    .select_related('temp_offer_solder') \
                    .select_related('temp_offer_products') \
                    .select_related('temp_offer_services') \
                    .prefetch_related('temp_offer_delivery') \
                    .filter(auth_shop=auth_shop).order_by('-created_date')
                page = self.paginate_queryset(queryset=offers)
                if page is not None:
                    serializer = BaseTempOfferssListSerializer(instance=page, many=True)
                    return self.get_paginated_response(serializer.data)
            except TempShop.DoesNotExist:
                errors = {"error": ["Shop not found."]}
                raise ValidationError(errors)
        # Real offers
        else:
            try:
                auth_shop = AuthShop.objects.get(user=user)
                shop_offers = Offers.objects \
                    .select_related('offer_solder') \
                    .select_related('offer_products') \
                    .select_related('offer_services') \
                    .prefetch_related('offer_delivery') \
                    .filter(auth_shop=auth_shop).order_by('-created_date')
                page = self.paginate_queryset(queryset=shop_offers)
                if page is not None:
                    serializer = BaseOffersListSerializer(instance=page, many=True)
                    return self.get_paginated_response(serializer.data)
            except AuthShop.DoesNotExist:
                errors = {"error": ["Shop not found."]}
                raise ValidationError(errors)


class GetOffersVuesListView(APIView, GetMyVuesPagination):
    permission_classes = (permissions.IsAuthenticated,)
    page_size = 10

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            shop_offers = Offers.objects.filter(auth_shop=auth_shop).select_related('offer_vues').annotate(
                nbr_total_vue=Count('offer_vues__nbr_total_vue'))
            page = self.paginate_queryset(request=request, queryset=shop_offers)
            # Replace None with zero
            total_vues = sum(filter(None, shop_offers.values_list('offer_vues__nbr_total_vue', flat=True)))
            if page is not None:
                serializer = BaseOffersVuesListSerializer(instance=page, many=True)
                response = sorted(list(serializer.data), reverse=True,
                                  key=lambda key_needed: key_needed['nbr_total_vue'])
                return self.get_paginated_response_custom(response, total_vues=total_vues, auth_shop=auth_shop)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopOfferSolderView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        offer_pk = kwargs.get('offer_pk')
        # Temp offers
        if user.is_anonymous:
            unique_id = kwargs.get('unique_id')
            try:
                solder = TempSolder.objects.get(offer=offer_pk, offer__auth_shop__unique_id=unique_id)
                offer_details_serializer = BaseTempShopOfferSolderSerializer(solder)
                return Response(offer_details_serializer.data, status=status.HTTP_200_OK)
            except TempSolder.DoesNotExist:
                errors = {"error": ["Offer solder not found."]}
                raise ValidationError(errors)
        # Real offers
        else:
            try:
                solder = Solder.objects.get(offer=offer_pk, offer__auth_shop__user=user)
                offer_details_serializer = BaseShopOfferSolderSerializer(solder)
                return Response(offer_details_serializer.data, status=status.HTTP_200_OK)
            except Solder.DoesNotExist:
                errors = {"error": ["Offer solder not found."]}
                raise ValidationError(errors)

    @staticmethod
    def post(request, *args, **kwargs):
        offer_pk = request.data.get('offer_pk')
        solder_type = request.data.get('solder_type')
        solder_value = request.data.get('solder_value')
        user = request.user
        # Temp offers
        if user.is_anonymous:
            unique_id = kwargs.get('unique_id')
            try:
                offer = TempOffers.objects.get(pk=offer_pk, auth_shop__unique_id=unique_id)
                if solder_type == 'F':
                    if float(solder_value) >= offer.price:
                        errors = {"error": ["Solder fix price is more than the offer price."]}
                        raise ValidationError(errors)
                if solder_type == 'P':
                    if float(solder_value) >= 100:
                        errors = {"error": ["Solder can't be applied up to 100%."]}
                        raise ValidationError(errors)
                serializer = BaseTempShopOfferSolderSerializer(data={
                    'offer': offer.pk,
                    'solder_type': solder_type,
                    'solder_value': float(solder_value),
                })
                if serializer.is_valid():
                    serializer.save()
                    return Response(data=serializer.data, status=status.HTTP_200_OK)
                raise ValidationError(serializer.errors)
            except TempOffers.DoesNotExist:
                errors = {"error": ["Offer not found."]}
                raise ValidationError(errors)
        # Real offers
        else:
            try:
                offer = Offers.objects.get(pk=offer_pk, auth_shop__user=user)
                if solder_type == 'F':
                    if float(solder_value) >= offer.price:
                        errors = {"error": ["Solder fix price is more than the offer price."]}
                        raise ValidationError(errors)
                if solder_type == 'P':
                    if float(solder_value) >= 100:
                        errors = {"error": ["Solder can't be applied up to 100%."]}
                        raise ValidationError(errors)
                serializer = BaseShopOfferSolderSerializer(data={
                    'offer': offer.pk,
                    'solder_type': solder_type,
                    'solder_value': float(solder_value),
                })
                if serializer.is_valid():
                    serializer.save()
                    return Response(data=serializer.data, status=status.HTTP_200_OK)
                raise ValidationError(serializer.errors)
            except Offers.DoesNotExist:
                errors = {"error": ["Offer not found."]}
                raise ValidationError(errors)

    @staticmethod
    def patch(request, *args, **kwargs):
        offer_pk = request.data.get('offer_pk')
        user = request.user
        # Temp offers
        if user.is_anonymous:
            unique_id = kwargs.get('unique_id')
            try:
                solder = TempSolder.objects.get(offer=offer_pk, offer__auth_shop__unique_id=unique_id)
                if solder.solder_type == 'F':
                    if solder.solder_value >= solder.offer.price:
                        errors = {"error": ["Solder fix price is more than the offer price."]}
                        raise ValidationError(errors)
                if solder.solder_type == 'P':
                    if solder.solder_value >= 100:
                        errors = {"error": ["Solder can't be applied up to 100%."]}
                        raise ValidationError(errors)
                serializer = BaseTempShopOfferSolderPutSerializer(solder, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    data = {
                        'offer': int(offer_pk),
                        'solder_type': serializer.data.get('solder_type'),
                        'solder_value': serializer.data.get('solder_value'),
                    }
                    return Response(data=data, status=status.HTTP_200_OK)
                raise ValidationError(serializer.errors)
            except TempSolder.DoesNotExist:
                errors = {"error": ["Solder not found."]}
                raise ValidationError(errors)
        # Real offers
        else:
            try:
                solder = Solder.objects.get(offer=offer_pk, offer__auth_shop__user=user)
                if solder.solder_type == 'F':
                    if solder.solder_value >= solder.offer.price:
                        errors = {"error": ["Solder fix price is more than the offer price."]}
                        raise ValidationError(errors)
                if solder.solder_type == 'P':
                    if solder.solder_value >= 100:
                        errors = {"error": ["Solder can't be applied up to 100%."]}
                        raise ValidationError(errors)
                serializer = BaseShopOfferSolderPutSerializer(solder, data=request.data, partial=True)
                if serializer.is_valid():
                    # serializer.update(solder, serializer.validated_data)
                    serializer.save()
                    data = {
                        'offer': int(offer_pk),
                        'solder_type': serializer.data.get('solder_type'),
                        'solder_value': serializer.data.get('solder_value'),
                    }
                    return Response(data=data, status=status.HTTP_200_OK)
                raise ValidationError(serializer.errors)
            except Solder.DoesNotExist:
                errors = {"error": ["Solder not found."]}
                raise ValidationError(errors)

    @staticmethod
    def delete(request, *args, **kwargs):
        offer_pk = kwargs.get('offer_pk')
        user = request.user
        # Temp offers
        if user.is_anonymous:
            unique_id = kwargs.get('unique_id')
            try:
                TempSolder.objects.get(offer=offer_pk, offer__auth_shop__unique_id=unique_id).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except TempSolder.DoesNotExist:
                errors = {"error": ["Solder not found."]}
                raise ValidationError(errors)
        # Real offers
        else:
            try:
                Solder.objects.get(offer=offer_pk, offer__auth_shop__user=user).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Solder.DoesNotExist:
                errors = {"error": ["Solder not found."]}
                raise ValidationError(errors)


class ShopOfferDuplicateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        offer_pk = request.data.get('offer_pk')
        try:
            offer = Offers.objects \
                .select_related('offer_solder') \
                .select_related('offer_products') \
                .select_related('offer_services') \
                .prefetch_related('offer_delivery') \
                .get(pk=offer_pk, auth_shop__user=user)
            # Title
            title = offer.title
            # Description
            description = offer.description
            # Price
            price = offer.price
            # Offer type
            offer_type = offer.offer_type
            offer_serializer = BaseShopOfferDuplicateSerializer(data={
                'auth_shop': offer.auth_shop.pk,
                'offer_type': offer_type,
                'title': title,
                'picture_1': offer.picture_1 if offer.picture_1 else None,
                'picture_2': offer.picture_2 if offer.picture_2 else None,
                'picture_3': offer.picture_3 if offer.picture_3 else None,
                'picture_1_thumbnail': offer.picture_1_thumbnail if offer.picture_1_thumbnail else None,
                'picture_2_thumbnail': offer.picture_2_thumbnail if offer.picture_2_thumbnail else None,
                'picture_3_thumbnail': offer.picture_3_thumbnail if offer.picture_3_thumbnail else None,
                'description': description,
                'price': price
            })
            if offer_serializer.is_valid():
                # Duplicate offer
                offer_serializer = offer_serializer.save()
                # Duplicate pictures
                base_duplicate_offer_images.apply_async((offer.pk, offer_serializer.pk, 'Offers'), )
                # Solder
                try:
                    product_solder = offer.offer_solder
                    solder_serializer = BaseShopOfferSolderSerializer(data={
                        'offer': offer_serializer.pk,
                        'solder_type': product_solder.solder_type,
                        'solder_value': product_solder.solder_value
                    })
                    if solder_serializer.is_valid():
                        solder_serializer.save()
                except ObjectDoesNotExist:
                    pass
                data = {
                    'pk': offer_serializer.pk,
                    'offer_type': offer_serializer.offer_type,
                    'title': offer_serializer.title,
                    'picture_1': offer_serializer.get_absolute_picture_1_img,
                    'picture_1_thumb': offer_serializer.get_absolute_picture_1_thumbnail,
                    'picture_2': offer_serializer.get_absolute_picture_2_img,
                    'picture_2_thumb': offer_serializer.get_absolute_picture_2_thumbnail,
                    'picture_3': offer_serializer.get_absolute_picture_3_img,
                    'picture_3_thumb': offer_serializer.get_absolute_picture_3_thumbnail,
                    'description': offer_serializer.description,
                    'price': offer_serializer.price
                }
                # Categories
                offer_categories = list(offer.offer_categories.all().values_list('pk', flat=True))
                offer_categories = Categories.objects.filter(pk__in=offer_categories)
                offer_categories_list = []
                for category in offer_categories:
                    offer_serializer.offer_categories.add(category.pk)
                    offer_categories_list.append(
                        {
                            "pk": category.pk,
                            "code_category": category.code_category,
                            "name_category": category.name_category
                        }
                    )
                data['offer_categories'] = offer_categories_list
                # For whom
                for_whom = list(offer.for_whom.all().values_list('pk', flat=True))
                for_whom = ForWhom.objects.filter(pk__in=for_whom)
                offer_for_whom_list = []
                for for_who in for_whom:
                    offer_serializer.for_whom.add(for_who.pk)
                    offer_for_whom_list.append(
                        {
                            "pk": for_who.pk,
                            "code_for_whom": for_who.code_for_whom,
                            "name_for_whom": for_who.name_for_whom
                        }
                    )
                data['for_whom'] = offer_for_whom_list
                # Duplicate Offer Tags
                tags = list(offer.tags.all().values_list('pk', flat=True))
                tags = OfferTags.objects.filter(pk__in=tags)
                tags_list = []
                for tag in tags:
                    offer_serializer.tags.add(tag.pk)
                    tags_list.append(
                        {
                            "pk": tag.pk,
                            "name_tag": tag.name_tag,
                        }
                    )
                data['tags'] = tags_list
                # Duplicate Product
                product_valid = False
                product_serializer_errors = None
                service_serializer_errors = None
                if offer_serializer.offer_type == 'V':
                    product_quantity = offer.offer_products.product_quantity
                    product_price_by = offer.offer_products.product_price_by
                    product_longitude = offer.offer_products.product_longitude
                    product_latitude = offer.offer_products.product_latitude
                    product_address = offer.offer_products.product_address
                    product_serializer = BaseShopProductSerializer(data={
                        'offer': offer_serializer.pk,
                        'product_quantity': product_quantity,
                        'product_price_by': product_price_by,
                        'product_longitude': product_longitude,
                        'product_latitude': product_latitude,
                        'product_address': product_address,
                    })
                    if product_serializer.is_valid():
                        product_valid = True
                        product_serializer.save()
                        # Color
                        colors = list(offer.offer_products.product_colors.all().values_list('pk', flat=True))
                        colors = Colors.objects.filter(pk__in=colors)
                        product_colors_list = []
                        for color in colors:
                            offer_serializer.offer_products.product_colors.add(color.pk)
                            product_colors_list.append(
                                {
                                    "pk": color.pk,
                                    "code_color": color.code_color,
                                    "name_color": color.name_color
                                }
                            )
                        data['product_colors'] = product_colors_list
                        # Size
                        sizes = list(offer.offer_products.product_sizes.all().values_list('pk', flat=True))
                        sizes = Sizes.objects.filter(pk__in=sizes)
                        product_sizes_list = []
                        for size in sizes:
                            offer_serializer.offer_products.product_sizes.add(size.pk)
                            product_sizes_list.append(
                                {
                                    "pk": size.pk,
                                    "code_color": size.code_size,
                                    "name_color": size.name_size
                                }
                            )
                        data['product_sizes'] = product_sizes_list
                    else:
                        product_serializer_errors = product_serializer.errors
                # Duplicate Service
                elif offer_serializer.offer_type == 'S':
                    service_morning_hour_from = offer.offer_services.service_morning_hour_from
                    service_morning_hour_to = offer.offer_services.service_morning_hour_to
                    service_afternoon_hour_from = offer.offer_services.service_afternoon_hour_from
                    service_afternoon_hour_to = offer.offer_services.service_afternoon_hour_to
                    service_zone_by = offer.offer_services.service_zone_by
                    service_price_by = offer.offer_services.service_price_by
                    service_longitude = offer.offer_services.service_longitude
                    service_latitude = offer.offer_services.service_latitude
                    service_address = offer.offer_services.service_address
                    service_serializer = BaseShopServiceSerializer(data={
                        'offer': offer_serializer.pk,
                        'service_morning_hour_from': service_morning_hour_from,
                        'service_morning_hour_to': service_morning_hour_to,
                        'service_afternoon_hour_from': service_afternoon_hour_from,
                        'service_afternoon_hour_to': service_afternoon_hour_to,
                        'service_zone_by': service_zone_by,
                        'service_price_by': service_price_by,
                        'service_longitude': service_longitude,
                        'service_latitude': service_latitude,
                        'service_address': service_address,
                    })
                    if service_serializer.is_valid():
                        service_serializer = service_serializer.save()
                        # Availability Days
                        availability_days = list(offer.offer_services.service_availability_days.all()
                                                 .values_list('pk', flat=True))
                        availability_days = ServiceDays.objects.filter(pk__in=availability_days)
                        service_availability_days_list = []
                        for availability_day in availability_days:
                            service_serializer.service_availability_days.add(availability_day.pk)
                            service_availability_days_list.append(
                                {
                                    "pk": availability_day.pk,
                                    "code_day": availability_day.code_day,
                                    "name_day": availability_day.name_day
                                }
                            )
                        data['service_availability_days'] = service_availability_days_list
                    else:
                        service_serializer_errors = service_serializer.errors
                if product_valid:
                    deliveries = offer.offer_delivery.all()
                    delivery_price_1 = None
                    delivery_days_1 = None
                    delivery_city_1 = None
                    delivery_price_2 = None
                    delivery_days_2 = None
                    delivery_city_2 = None
                    delivery_price_3 = None
                    delivery_days_3 = None
                    delivery_city_3 = None
                    try:
                        delivery_price_1 = deliveries[0].delivery_price
                        delivery_days_1 = deliveries[0].delivery_days
                        delivery_city_1 = deliveries[0].delivery_city.all().values_list('pk', flat=True)
                        delivery_price_2 = deliveries[1].delivery_price
                        delivery_days_2 = deliveries[1].delivery_days
                        delivery_city_2 = deliveries[1].delivery_city.all().values_list('pk', flat=True)
                        delivery_price_3 = deliveries[2].delivery_price
                        delivery_days_3 = deliveries[2].delivery_days
                        delivery_city_3 = deliveries[2].delivery_city.all().values_list('pk', flat=True)
                    except IndexError:
                        pass
                    # Delivery 1 cities
                    delivery_cities_1_pk = []
                    delivery_cities_1 = []
                    if delivery_city_1:
                        cities = City.objects.filter(pk__in=delivery_city_1)
                        for city in cities:
                            delivery_cities_1.append(
                                {
                                    "pk": city.pk,
                                    "city": city.name_fr,
                                }
                            )
                            delivery_cities_1_pk.append(
                                city.pk
                            )
                    # Delivery 2 cities
                    delivery_cities_2_pk = []
                    delivery_cities_2 = []
                    if delivery_city_2:
                        cities = City.objects.filter(pk__in=delivery_city_2)
                        for city in cities:
                            delivery_cities_2.append(
                                {
                                    "pk": city.pk,
                                    "city": city.name_fr,
                                }
                            )
                            delivery_cities_2_pk.append(
                                city.pk
                            )
                    # Delivery 3 cities
                    delivery_cities_3_pk = []
                    delivery_cities_3 = []
                    if delivery_city_3:
                        cities = City.objects.filter(pk__in=delivery_city_3)
                        for city in cities:
                            delivery_cities_3.append(
                                {
                                    "pk": city.pk,
                                    "city": city.name_fr,
                                }
                            )
                            delivery_cities_3_pk.append(
                                city.pk
                            )
                    deliveries = []
                    city_1_check = False
                    city_2_check = False
                    city_3_check = False
                    if delivery_city_1:
                        city_1_check = True
                        deliveries.append(
                            {
                                'delivery_city': delivery_cities_1,
                                'delivery_price': float(delivery_price_1),
                                'delivery_days': int(delivery_days_1)
                            }
                        )
                    if delivery_city_2:
                        city_2_check = True
                        deliveries.append(
                            {
                                'delivery_city': delivery_cities_2,
                                'delivery_price': float(delivery_price_2),
                                'delivery_days': int(delivery_days_2)
                            }
                        )
                    if delivery_city_3:
                        city_3_check = True
                        deliveries.append(
                            {
                                'delivery_city': delivery_cities_3,
                                'delivery_price': float(delivery_price_3),
                                'delivery_days': int(delivery_days_3)
                            }
                        )
                    delivery_serializer = BaseShopDeliverySerializer(data=deliveries, many=True)
                    if delivery_serializer.is_valid():
                        deliveries_serializer = delivery_serializer.save()
                        for delivery in deliveries_serializer:
                            if city_1_check:
                                delivery.delivery_city.add(*delivery_cities_1_pk)
                                city_1_check = False
                            elif city_2_check:
                                delivery.delivery_city.add(*delivery_cities_2_pk)
                                city_2_check = False
                            elif city_3_check:
                                delivery.delivery_city.add(*delivery_cities_3_pk)
                                city_3_check = False
                        data['deliveries'] = deliveries
                        return Response(data=data, status=status.HTTP_200_OK)
                    else:
                        raise ValidationError(delivery_serializer.errors)
                else:
                    offer_serializer.delete()
                    if offer_type == 'V' and product_serializer_errors:
                        raise ValidationError(product_serializer_errors)
                    if offer_type == 'S' and service_serializer_errors:
                        raise ValidationError(service_serializer_errors)
            raise ValidationError(offer_serializer.errors)
        except Offers.DoesNotExist:
            errors = {"error": ["Offer not found."]}
            raise ValidationError(errors)


class GetLastThreeDeliveriesView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        # Temp offers
        if user.is_anonymous:
            unique_id = kwargs.get('unique_id')
            try:
                auth_shop = TempShop.objects.get(unique_id=unique_id)
                offers = TempOffers.objects \
                    .select_related('temp_offer_products') \
                    .prefetch_related('temp_offer_delivery') \
                    .filter(auth_shop=auth_shop).order_by('-created_date')
                data = defaultdict(list)
                for offer in offers:
                    deliveries = offer.temp_offer_delivery.all().order_by('-pk')
                    for delivery in deliveries:
                        deliveries_list = {
                            'pk': '',
                            'delivery_city': '',
                            'delivery_price': '',
                            'delivery_days': '',
                        }
                        dict_title = "deliveries"
                        deliveries_list['pk'] = delivery.pk
                        deliveries_list['delivery_city'] = delivery.delivery_city.all() \
                            .values_list('name_fr', flat=True)
                        deliveries_list['delivery_price'] = delivery.delivery_price
                        deliveries_list['delivery_days'] = delivery.delivery_days
                        data[dict_title].append(deliveries_list)
                        if len(data['deliveries']) == 3:
                            break
                    if len(data['deliveries']) == 3:
                        break
                return Response(data, status=status.HTTP_200_OK)
            except TempShop.DoesNotExist:
                errors = {"error": ["Shop not found."]}
                raise ValidationError(errors)
        # Real offers
        else:
            try:
                auth_shop = AuthShop.objects.get(user=user)
                offers = Offers.objects \
                    .select_related('offer_products') \
                    .prefetch_related('offer_delivery') \
                    .filter(auth_shop=auth_shop).order_by('-created_date')
                data = defaultdict(list)
                for offer in offers:
                    deliveries = offer.offer_delivery.all().order_by('-pk')
                    for delivery in deliveries:
                        delivery_cities = delivery.delivery_city.all().values('pk', name_=F('name_fr'))
                        delivery_city = []
                        for i in delivery_cities:
                            delivery_obj = {'pk': '', 'name': ''}
                            for k, v in i.items():
                                if k == 'name_':
                                    delivery_obj['name'] = v
                                else:
                                    delivery_obj[k] = v
                            delivery_city.append(delivery_obj)
                        deliveries_list = {
                            'pk': '',
                            'delivery_city': '',
                            'delivery_price': '',
                            'delivery_days': '',
                        }
                        dict_title = "deliveries"
                        deliveries_list['pk'] = delivery.pk
                        deliveries_list['delivery_city'] = delivery_city
                        deliveries_list['delivery_price'] = delivery.delivery_price
                        deliveries_list['delivery_days'] = delivery.delivery_days
                        data[dict_title].append(deliveries_list)
                        if len(data['deliveries']) == 3:
                            break
                    if len(data['deliveries']) == 3:
                        break
                return Response(data, status=status.HTTP_200_OK)
            except AuthShop.DoesNotExist:
                errors = {"error": ["Shop not found."]}
                raise ValidationError(errors)


class GetLastUsedLocalisationView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        offer_type = kwargs.get('offer_type')
        user = request.user
        # Temp offers
        if user.is_anonymous:
            unique_id = kwargs.get('unique_id')
            try:
                auth_shop = TempShop.objects.get(unique_id=unique_id)
                offer = TempOffers.objects \
                    .select_related('temp_offer_products') \
                    .select_related('temp_offer_services') \
                    .prefetch_related('temp_offer_delivery') \
                    .filter(auth_shop=auth_shop).order_by('-created_date').last()
                if offer:
                    data_product = {
                        'longitude': None,
                        'latitude': None,
                        'localisation_name': None,
                    }
                    data_service = {
                        'zone_by': None,
                        'longitude': None,
                        'latitude': None,
                        'km_radius': None,
                        'localisation_name': None,
                    }
                    if offer.offer_type == offer_type:
                        if offer.temp_offer_products.product_address:
                            data_product['longitude'] = offer.temp_offer_products.product_longitude
                            data_product['latitude'] = offer.temp_offer_products.product_latitude
                            data_product['localisation_name'] = offer.temp_offer_products.product_address
                            return Response(data=data_product, status=status.HTTP_200_OK)
                    elif offer.offer_type == offer_type:
                        if offer.temp_offer_services.service_address:
                            data_service['zone_by'] = offer.temp_offer_services.service_zone_by
                            data_service['longitude'] = offer.temp_offer_services.service_longitude
                            data_service['latitude'] = offer.temp_offer_services.service_latitude
                            data_service['km_radius'] = offer.temp_offer_services.service_km_radius
                            data_service['localisation_name'] = offer.temp_offer_services.service_address
                            return Response(data=data_service, status=status.HTTP_200_OK)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response(status=status.HTTP_204_NO_CONTENT)
            except TempOffers.DoesNotExist:
                errors = {"error": ["Offer not found."]}
                raise ValidationError(errors)
        # Real offers
        else:
            try:
                auth_shop = AuthShop.objects.get(user=user)
                offer = Offers.objects \
                    .select_related('offer_products') \
                    .select_related('offer_services') \
                    .prefetch_related('offer_delivery') \
                    .filter(auth_shop=auth_shop).order_by('-created_date').last()
                if offer:
                    data_product = {
                        'longitude': None,
                        'latitude': None,
                        'localisation_name': None,
                    }
                    data_service = {
                        'zone_by': None,
                        'longitude': None,
                        'latitude': None,
                        'km_radius': None,
                        'localisation_name': None,
                    }
                    if offer.offer_type == offer_type:
                        if offer.offer_products.product_address:
                            data_product['longitude'] = offer.offer_products.product_longitude
                            data_product['latitude'] = offer.offer_products.product_latitude
                            data_product['localisation_name'] = offer.offer_products.product_address
                            return Response(data=data_product, status=status.HTTP_200_OK)
                    elif offer.offer_type == offer_type:
                        if offer.offer_services.service_address:
                            data_service['zone_by'] = offer.offer_services.service_zone_by
                            data_service['longitude'] = offer.offer_services.service_longitude
                            data_service['latitude'] = offer.offer_services.service_latitude
                            data_service['km_radius'] = offer.offer_services.service_km_radius
                            data_service['localisation_name'] = offer.offer_services.service_address
                            return Response(data=data_service, status=status.HTTP_200_OK)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response(status=status.HTTP_204_NO_CONTENT)
            except AuthShop.DoesNotExist:
                errors = {"error": ["Shop not found."]}
                raise ValidationError(errors)


class GetOfferTagsView(ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = OfferTags.objects.all()
    serializer_class = BaseOfferTagsSerializer
    filter_class = TagsFilterSet
    pagination_class = None

    def get_queryset(self):
        if not self.request.GET.get('name_tag'):
            return self.queryset.model.objects.none()
        else:
            self.filter_class = TagsFilterSet
            self.serializer_class = BaseOfferTagsSerializer
            return super().get_queryset()

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     serializer = self.get_serializer(queryset, many=True)
    #     data = []
    #     for obj in serializer.data:
    #         for k, v in obj.items():
    #             data.append(v)
    #     # return Response({'name_tag': data})
    #     return Response(data=data, status=status.HTTP_200_OK)
