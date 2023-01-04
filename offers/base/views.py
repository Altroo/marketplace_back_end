from collections import defaultdict
from typing import Union
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.db.models import Count, F, QuerySet
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from offers.models import AuthShop, Offers, Solder, Products, Services, Delivery, OfferTags, \
    Categories, Colors, Sizes, ForWhom, ServiceDays, OfferVue, OffersTotalVues
from offers.base.serializers import BaseShopOfferSerializer, \
    BaseShopDeliverySerializer, BaseOfferDetailsSerializer, \
    BaseOffersListSerializer, BaseShopOfferSolderSerializer, \
    BaseShopOfferSolderPutSerializer, BaseShopProductSerializer, \
    BaseShopServiceSerializer, BaseProductPutSerializer, \
    BaseServicePutSerializer, BaseOfferPutSerializer, \
    BaseShopOfferDuplicateSerializer, BaseOfferTagsSerializer, \
    BaseOffersVuesListSerializer
from offers.base.filters import TagsFilterSet, BaseOffersListSortByPrice
from os import path, remove
from Qaryb_API.settings import API_URL
from offers.base.tasks import base_duplicate_offer_images, base_duplicate_offervue_images, base_resize_offer_images
from places.models import City, Country
from offers.base.pagination import GetMyVuesPagination
from datetime import datetime
from shop.base.utils import ImageProcessor


class ShopOfferViewV2(APIView):
    permission_classes = (permissions.AllowAny,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def get(request, *args, **kwargs):
        offer_pk = kwargs.get('offer_pk')
        shop_link = kwargs.get('shop_link')
        unique_id = kwargs.get('unique_id')
        # user = request.user
        # with the link
        if shop_link:
            try:
                shop = AuthShop.objects.get(qaryb_link=shop_link)
                try:
                    offer = Offers.objects \
                        .select_related('offer_solder') \
                        .select_related('offer_products') \
                        .select_related('offer_services') \
                        .prefetch_related('offer_delivery') \
                        .get(pk=offer_pk, auth_shop=shop)
                    offer_details_serializer = BaseOfferDetailsSerializer(offer, context={'unique_id': unique_id})
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
            except AuthShop.DoesNotExist:
                errors = {"error": ["Shop not found."]}
                raise ValidationError(errors)
        else:
            try:
                offer = Offers.objects \
                    .select_related('offer_solder') \
                    .select_related('offer_products') \
                    .select_related('offer_services') \
                    .prefetch_related('offer_delivery') \
                    .get(pk=offer_pk)
                offer_details_serializer = BaseOfferDetailsSerializer(offer, context={'unique_id': unique_id})
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
        try:
            auth_shop = AuthShop.objects.get(user=user)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)
        offer_type = request.data.get('offer_type')
        title = request.data.get('title')
        description = request.data.get('description')
        price = request.data.get('price')
        made_in_label = request.data.get('made_in_label')
        try:
            made_in_label = Country.objects.get(name_fr=made_in_label)
        except Country.DoesNotExist:
            made_in_label = None
        if auth_shop.creator:
            creator_label = request.data.get('creator_label', False)
        else:
            creator_label = False

        image_processor = ImageProcessor()
        picture_1_file: ContentFile | None = image_processor.data_url_to_uploaded_file(request.data.get('picture_1'))
        picture_2_file: ContentFile | None = image_processor.data_url_to_uploaded_file(request.data.get('picture_2'))
        picture_3_file: ContentFile | None = image_processor.data_url_to_uploaded_file(request.data.get('picture_3'))
        picture_4_file: ContentFile | None = image_processor.data_url_to_uploaded_file(request.data.get('picture_4'))

        thumbnail_1_file: ContentFile | None = image_processor.data_url_to_uploaded_file(
            request.data.get('thumbnail_1'))
        thumbnail_2_file: ContentFile | None = image_processor.data_url_to_uploaded_file(
            request.data.get('thumbnail_2'))
        thumbnail_3_file: ContentFile | None = image_processor.data_url_to_uploaded_file(
            request.data.get('thumbnail_3'))
        thumbnail_4_file: ContentFile | None = image_processor.data_url_to_uploaded_file(
            request.data.get('thumbnail_4'))

        offer_serializer = BaseShopOfferSerializer(data={
            'auth_shop': auth_shop.pk,
            'offer_type': offer_type,
            # Categories
            'title': title,
            'picture_1': None,
            'picture_1_thumbnail': None,
            'picture_2': None,
            'picture_2_thumbnail': None,
            'picture_3': None,
            'picture_3_thumbnail': None,
            'picture_4': None,
            'picture_4_thumbnail': None,
            'description': description,
            'creator_label': creator_label,
            'made_in_label': made_in_label.pk if made_in_label else None,
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
            # base_generate_offer_thumbnails.apply_async((offer_pk, ), )
            base_resize_offer_images.apply_async((
                offer_pk,
                picture_1_file.file if isinstance(picture_1_file, ContentFile) else None,
                thumbnail_1_file.file if isinstance(thumbnail_1_file, ContentFile) else None,
                picture_2_file.file if isinstance(picture_2_file, ContentFile) else None,
                thumbnail_2_file.file if isinstance(thumbnail_2_file, ContentFile) else None,
                picture_3_file.file if isinstance(picture_3_file, ContentFile) else None,
                thumbnail_3_file.file if isinstance(thumbnail_3_file, ContentFile) else None,
                picture_4_file.file if isinstance(picture_4_file, ContentFile) else None,
                thumbnail_4_file.file if isinstance(thumbnail_4_file, ContentFile) else None,
            ), )
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
                'picture_4': offer.get_absolute_picture_4_img,
                'picture_4_thumb': offer.get_absolute_picture_4_thumbnail,
                'description': description,
                'made_in_label': {
                    'name': made_in_label.name_fr if made_in_label else None,
                    'code': made_in_label.code if made_in_label else None,
                },
                'creator_label': creator_label,
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
            # if request.data.get('tags') is not None:
            #     tags = str(request.data.get('tags')).split(',')
            #     for tag in tags:
            #         try:
            #             OfferTags.objects.create(name_tag=tag)
            #         except IntegrityError:
            #             pass
            #     tags = OfferTags.objects.filter(name_tag__in=tags)
            #     tags_list = []
            #     for tag in tags:
            #         offer.tags.add(tag.pk)
            #         # tags_list.append(tag.name_tag)
            #         tags_list.append(
            #             {
            #                 "pk": tag.pk,
            #                 "name_tag": tag.name_tag,
            #             }
            #         )
            #     data['tags'] = tags_list
            # else:
            #     # Return empty tags
            #     data['tags'] = []
            # IF OFFER TYPE == V (VENTE) ; S (SERVICE)
            if offer_type == 'V':
                product_quantity = request.data.get('product_quantity')
                if product_quantity == 'null':
                    product_quantity = None
                product_price_by = request.data.get('product_price_by')
                product_longitude = request.data.get('product_longitude')
                product_latitude = request.data.get('product_latitude')
                product_address = request.data.get('product_address')
                if product_latitude == 'null':
                    product_longitude = None
                    product_latitude = None
                    product_address = None
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
                if service_afternoon_hour_from == 'null':
                    service_afternoon_hour_from = None
                if service_afternoon_hour_to == 'null':
                    service_afternoon_hour_to = None
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
                all_cities_1 = request.data.get('all_cities_1', None)
                delivery_price_1 = request.data.get('delivery_price_1', None)
                delivery_days_1 = request.data.get('delivery_days_1', None)

                all_cities_2 = request.data.get('all_cities_2', None)
                delivery_price_2 = request.data.get('delivery_price_2', None)
                delivery_days_2 = request.data.get('delivery_days_2', None)

                all_cities_3 = request.data.get('all_cities_3', None)
                delivery_price_3 = request.data.get('delivery_price_3', None)
                delivery_days_3 = request.data.get('delivery_days_3', None)

                # Delivery 1 cities
                delivery_city_1 = request.data.get('delivery_city_1')
                delivery_cities_1_pk = []
                delivery_cities_1 = []
                if delivery_city_1 is not None and delivery_city_1 != 'null' and delivery_city_1 != '':
                    cities_str = str(delivery_city_1).split(',')
                    cities = []
                    for city in cities_str:
                        cities.append(str(city))

                    cities = City.objects.filter(name_fr__in=cities)
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
                if delivery_city_2 is not None and delivery_city_2 != 'null' and delivery_city_2 != '':
                    cities_str = str(delivery_city_2).split(',')
                    cities = []
                    for city in cities_str:
                        cities.append(str(city))

                    cities = City.objects.filter(name_fr__in=cities)
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
                if delivery_city_3 is not None and delivery_city_3 != 'null' and delivery_city_3 != '':
                    cities_str = str(delivery_city_3).split(',')
                    cities = []
                    for city in cities_str:
                        cities.append(str(city))

                    cities = City.objects.filter(name_fr__in=cities)
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
                if delivery_city_1 is not None and delivery_city_1 != 'null' and delivery_city_1 != '' \
                        or all_cities_1 == 'true':
                    city_1_check = True
                    deliveries.append(
                        {
                            'offer': offer_pk,
                            'pk': offer_pk,
                            'delivery_city': delivery_cities_1,
                            'all_cities': True if all_cities_1 == 'true' else False,
                            'delivery_price': float(delivery_price_1),
                            'delivery_days': int(delivery_days_1)
                        }
                    )
                if delivery_city_2 is not None and delivery_city_2 != 'null' and delivery_city_2 != '' \
                        or all_cities_2 == 'true':
                    city_2_check = True
                    deliveries.append(
                        {
                            'offer': offer_pk,
                            'pk': offer_pk,
                            'delivery_city': delivery_cities_2,
                            'all_cities': True if all_cities_2 == 'true' else False,
                            'delivery_price': float(delivery_price_2),
                            'delivery_days': int(delivery_days_2)
                        }
                    )
                if delivery_city_3 is not None and delivery_city_3 != 'null' and delivery_city_3 != '' \
                        or all_cities_3 == 'true':
                    city_3_check = True
                    deliveries.append(
                        {
                            'offer': offer_pk,
                            'pk': offer_pk,
                            'delivery_city': delivery_cities_3,
                            'all_cities': True if all_cities_3 == 'true' else False,
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
                    raise ValidationError(product_serializer_errors)
                if offer_type == 'S' and service_serializer_errors:
                    raise ValidationError(service_serializer_errors)
        raise ValidationError(offer_serializer.errors)

    @staticmethod
    def correct_image_index(picture_file: ContentFile | None,
                            offer: Union[QuerySet, Offers],
                            picture_name: str,
                            picture_data,
                            previous_images: list[Union[str, None]]):

        if not isinstance(picture_file, ContentFile):
            if picture_data in previous_images:
                try:
                    picture_index = previous_images.index(picture_data)
                    if picture_index == 0:
                        picture = offer.picture_1
                    elif picture_index == 1:
                        picture = offer.picture_2
                    elif picture_index == 2:
                        picture = offer.picture_3
                    else:
                        picture = offer.picture_4
                # None wasn't sent
                except ValueError:
                    picture = None
                setattr(offer, picture_name, picture)
                offer.save(update_fields=[picture_name])
            else:
                setattr(offer, picture_name, None)
                offer.save(update_fields=[picture_name])

    def put(self, request, *args, **kwargs):
        offer_pk = request.data.get('offer_pk')
        user = request.user
        try:
            offer: Union[QuerySet, Offers] = Offers.objects.get(pk=offer_pk, auth_shop__user=user)
            offer_pk = offer.pk
            picture_1 = request.data.get('picture_1')
            thumbnail_1 = request.data.get('thumbnail_1')
            picture_2 = request.data.get('picture_2')
            thumbnail_2 = request.data.get('thumbnail_2')
            picture_3 = request.data.get('picture_3')
            thumbnail_3 = request.data.get('thumbnail_3')
            picture_4 = request.data.get('picture_4')
            thumbnail_4 = request.data.get('thumbnail_4')

            image_processor = ImageProcessor()

            picture_1_file = None
            if str(picture_1) != 'null':
                if not str(picture_1).startswith('http'):
                    picture_1_file: ContentFile | None = image_processor.data_url_to_uploaded_file(picture_1)

            picture_2_file = None
            if str(picture_2) != 'null':
                if not str(picture_2).startswith('http'):
                    picture_2_file: ContentFile | None = image_processor.data_url_to_uploaded_file(picture_2)

            picture_3_file = None
            if str(picture_3) != 'null':
                if not str(picture_3).startswith('http'):
                    picture_3_file: ContentFile | None = image_processor.data_url_to_uploaded_file(picture_3)

            picture_4_file = None
            if str(picture_4) != 'null':
                if not str(picture_4).startswith('http'):
                    picture_4_file: ContentFile | None = image_processor.data_url_to_uploaded_file(picture_4)

            thumbnail_1_file = None
            if str(thumbnail_1) != 'null':
                if not str(thumbnail_1).startswith('http'):
                    thumbnail_1_file: ContentFile | None = image_processor.data_url_to_uploaded_file(thumbnail_1)

            thumbnail_2_file = None
            if str(thumbnail_2) != 'null':
                if not str(thumbnail_2).startswith('http'):
                    thumbnail_2_file: ContentFile | None = image_processor.data_url_to_uploaded_file(thumbnail_2)

            thumbnail_3_file = None
            if str(thumbnail_3) != 'null':
                if not str(thumbnail_3).startswith('http'):
                    thumbnail_3_file: ContentFile | None = image_processor.data_url_to_uploaded_file(thumbnail_3)

            thumbnail_4_file = None
            if str(thumbnail_4) != 'null':
                if not str(thumbnail_4).startswith('http'):
                    thumbnail_4_file: ContentFile | None = image_processor.data_url_to_uploaded_file(thumbnail_4)

            if thumbnail_1_file is None:
                offer.picture_1_thumbnail = None
                offer.save(update_fields=['picture_1_thumbnail'])

            if thumbnail_2_file is None:
                offer.picture_2_thumbnail = None
                offer.save(update_fields=['picture_2_thumbnail'])

            if thumbnail_3_file is None:
                offer.picture_3_thumbnail = None
                offer.save(update_fields=['picture_3_thumbnail'])

            if thumbnail_4_file is None:
                offer.picture_4_thumbnail = None
                offer.save(update_fields=['picture_4_thumbnail'])

            previous_images = list()
            previous_images.append(API_URL + '/media' + offer.picture_1.url
                                   if offer.picture_1 else False)
            previous_images.append(API_URL + '/media' + offer.picture_2.url
                                   if offer.picture_2 else False)
            previous_images.append(API_URL + '/media' + offer.picture_3.url
                                   if offer.picture_3 else False)
            previous_images.append(API_URL + '/media' + offer.picture_4.url
                                   if offer.picture_4 else False)

            self.correct_image_index(picture_1_file, offer, 'picture_1', picture_1, previous_images)
            self.correct_image_index(picture_2_file, offer, 'picture_2', picture_2, previous_images)
            self.correct_image_index(picture_3_file, offer, 'picture_3', picture_3, previous_images)
            self.correct_image_index(picture_4_file, offer, 'picture_4', picture_4, previous_images)

            title = request.data.get('title', '')
            description = request.data.get('description', '')
            price = request.data.get('price', '')
            made_in_label = request.data.get('made_in_label', None)
            if made_in_label is not None:
                try:
                    made_in_label = Country.objects.get(name_fr=made_in_label)
                except Country.DoesNotExist:
                    pass
            if offer.auth_shop.creator:
                creator_label = request.data.get('creator_label', False)
            else:
                creator_label = False
            # Product PUT serializer
            offer_serializer = BaseOfferPutSerializer(data={
                'title': title,
                'description': description,
                'creator_label': creator_label,
                'made_in_label': made_in_label.pk if made_in_label else None,
                'price': price,
            }, partial=True)
            if offer_serializer.is_valid():
                offer_type = offer.offer_type
                product_valid = False
                service_valid = False
                product_serializer_errors = None
                service_serializer_errors = None
                product_serializer = None
                service_serializer = None
                if offer.offer_type == 'V':
                    product_quantity = request.data.get('product_quantity')
                    if product_quantity == 'null':
                        product_quantity = None
                    product_price_by = request.data.get('product_price_by', '')
                    product_longitude = request.data.get('product_longitude', '')
                    product_latitude = request.data.get('product_latitude', '')
                    product_address = request.data.get('product_address', '')
                    if product_latitude == 'null':
                        product_longitude = None
                        product_latitude = None
                        product_address = None
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
                    if service_afternoon_hour_from == 'null':
                        service_afternoon_hour_from = None
                    if service_afternoon_hour_to == 'null':
                        service_afternoon_hour_to = None
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
                    # Regenerate images
                    base_resize_offer_images.apply_async((
                        offer_pk,
                        picture_1_file.file if isinstance(picture_1_file, ContentFile) else None,
                        thumbnail_1_file.file if isinstance(thumbnail_1_file, ContentFile) else None,
                        picture_2_file.file if isinstance(picture_2_file, ContentFile) else None,
                        thumbnail_2_file.file if isinstance(thumbnail_2_file, ContentFile) else None,
                        picture_3_file.file if isinstance(picture_3_file, ContentFile) else None,
                        thumbnail_3_file.file if isinstance(thumbnail_3_file, ContentFile) else None,
                        picture_4_file.file if isinstance(picture_4_file, ContentFile) else None,
                        thumbnail_4_file.file if isinstance(thumbnail_4_file, ContentFile) else None,
                    ), )

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
                        'picture_4': updated_offer.get_absolute_picture_4_img,
                        'picture_4_thumb': updated_offer.get_absolute_picture_4_thumbnail,
                        'description': updated_offer.description,
                        'creator_label': updated_offer.creator_label,
                        'made_in_label': {
                            'name': updated_offer.made_in_label.name_fr if updated_offer.made_in_label else None,
                            'code': updated_offer.made_in_label.code if updated_offer.made_in_label else None,
                        },
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

                        all_cities_1 = request.data.get('all_cities_1', None)
                        delivery_price_1 = request.data.get('delivery_price_1', None)
                        delivery_days_1 = request.data.get('delivery_days_1', None)

                        all_cities_2 = request.data.get('all_cities_2', None)
                        delivery_price_2 = request.data.get('delivery_price_2', None)
                        delivery_days_2 = request.data.get('delivery_days_2', None)

                        all_cities_3 = request.data.get('all_cities_3', None)
                        delivery_price_3 = request.data.get('delivery_price_3', None)
                        delivery_days_3 = request.data.get('delivery_days_3', None)

                        # Delivery 1 cities
                        delivery_city_1 = request.data.get('delivery_city_1')
                        delivery_cities_1_pk = []
                        delivery_cities_1 = []
                        if delivery_city_1 is not None and delivery_city_1 != 'null' and delivery_city_1 != '':
                            cities_str = str(delivery_city_1).split(',')
                            cities = []
                            for city in cities_str:
                                cities.append(str(city))

                            cities = City.objects.filter(name_fr__in=cities)
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
                        if delivery_city_2 is not None and delivery_city_2 != 'null' and delivery_city_2 != '':
                            cities_str = str(delivery_city_2).split(',')
                            cities = []
                            for city in cities_str:
                                cities.append(str(city))

                            cities = City.objects.filter(name_fr__in=cities)
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
                        if delivery_city_3 is not None and delivery_city_3 != 'null' and delivery_city_3 != '':
                            cities_str = str(delivery_city_3).split(',')
                            cities = []
                            for city in cities_str:
                                cities.append(str(city))

                            cities = City.objects.filter(name_fr__in=cities)
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
                        if delivery_city_1 is not None and delivery_city_1 != 'null' and delivery_city_1 != '' \
                                or all_cities_1 == 'true':
                            city_1_check = True
                            deliveries.append(
                                {
                                    'offer': offer_pk,
                                    'pk': offer_pk,
                                    'delivery_city': delivery_cities_1,
                                    'all_cities': True if all_cities_1 == 'true' else False,
                                    'delivery_price': float(delivery_price_1),
                                    'delivery_days': int(delivery_days_1)
                                }
                            )
                        if delivery_city_2 is not None and delivery_city_2 != 'null' and delivery_city_2 != '' \
                                or all_cities_2 == 'true':
                            city_2_check = True
                            deliveries.append(
                                {
                                    'offer': offer_pk,
                                    'pk': offer_pk,
                                    'delivery_city': delivery_cities_2,
                                    'all_cities': True if all_cities_2 == 'true' else False,
                                    'delivery_price': float(delivery_price_2),
                                    'delivery_days': int(delivery_days_2)
                                }
                            )
                        if delivery_city_3 is not None and delivery_city_3 != 'null' and delivery_city_3 != '' \
                                or all_cities_3 == 'true':
                            city_3_check = True
                            deliveries.append(
                                {
                                    'offer': offer_pk,
                                    'pk': offer_pk,
                                    'delivery_city': delivery_cities_3,
                                    'all_cities': True if all_cities_3 == 'true' else False,
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
                                    "code_day": availability_day.code_day,
                                    "name_day": availability_day.name_day
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
                # Picture 4
                try:
                    picture_4 = offer.picture_4.path
                    remove(picture_4)
                except (FileNotFoundError, ValueError, AttributeError):
                    pass
                # Picture 4 thumbnail
                try:
                    picture_4_thumbnail = offer.picture_4_thumbnail.path
                    remove(picture_4_thumbnail)
                except (FileNotFoundError, ValueError, AttributeError):
                    pass
                offer.delete()
                deleted = True
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            errors = {"error": ["Offer not yours to delete."]}
            raise ValidationError(errors)


class GetMyShopOffersListView(APIView, PageNumberPagination):
    permission_classes = (permissions.AllowAny,)
    page_size = 20

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            shop_offers = Offers.objects \
                .select_related('offer_solder') \
                .select_related('offer_products') \
                .select_related('offer_services') \
                .prefetch_related('offer_delivery') \
                .filter(auth_shop=auth_shop).order_by('-pinned', '-created_date')
            page = self.paginate_queryset(queryset=shop_offers, request=request)
            if page is not None:
                serializer = BaseOffersListSerializer(instance=page, many=True)
                return self.get_paginated_response(serializer.data)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class GetShopOffersListView(ListAPIView, PageNumberPagination):
    permission_classes = (permissions.AllowAny,)
    filterset_class = BaseOffersListSortByPrice
    http_method_names = ('get',)
    serializer_class = BaseOffersListSerializer
    page_size = 20

    queryset = Offers.objects.all().select_related('offer_solder') \
        .select_related('offer_products') \
        .select_related('offer_services') \
        .prefetch_related('offer_delivery')

    def get_queryset(self) -> Union[QuerySet, None]:
        shop_pk: int = self.kwargs['shop_pk']
        try:
            auth_shop = AuthShop.objects.get(pk=shop_pk)
            queryset = super().get_queryset().filter(auth_shop=auth_shop)
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
        except AuthShop.DoesNotExist:
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

    # def custom_paginate_queryset(self, queryset):
    #     """
    #     Return a single page of results, or `None` if pagination is disabled.
    #     """
    #     if self.paginator is None:
    #         return None
    #     return self.paginator.paginate_queryset(queryset.order_by('-pinned'), self.request, view=self)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset is None:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)
        filter_queryset: QuerySet = self.filter_queryset(queryset)
        # page = self.custom_paginate_queryset(filter_queryset)
        page = self.paginate_queryset(filter_queryset)
        if page is not None:
            serializer: BaseOffersListSerializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['results'].sort(reverse=True, key=lambda key_needed: key_needed['pinned'])
            return response


class GetShopOffersFiltersListView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        auth_shop: int = self.kwargs['shop_pk']
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
            auth_shop_obj = AuthShop.objects.get(pk=auth_shop)
            offers = Offers.objects \
                .select_related('offer_products', 'offer_services', 'offer_solder') \
                .prefetch_related('offer_categories', 'for_whom', 'made_in_label', 'offer_delivery') \
                .filter(auth_shop=auth_shop_obj)
            # type hint
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
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopOfferPinUnpinView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        offer_pk = kwargs.get('offer_pk')
        try:
            offer = Offers.objects.get(pk=offer_pk, auth_shop__user=user)
            offer.pinned = not offer.pinned
            offer.save()
            data = {
                'offer_pk': offer.pk,
                'pinned': offer.pinned,
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except Offers.DoesNotExist:
            errors = {"error": ["Offer not found."]}
            raise ValidationError(errors)


class GetOffersVuesListView(APIView, GetMyVuesPagination):
    permission_classes = (permissions.IsAuthenticated,)
    page_size = 10

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            shop_offers = Offers.objects.filter(auth_shop=auth_shop).select_related('offer_vues') \
                .order_by(F('offer_vues__nbr_total_vue').desc(nulls_last=True)).annotate(
                nbr_total_vue=Count('offer_vues__nbr_total_vue'))
            total_vues = sum(filter(None, shop_offers.values_list('offer_vues__nbr_total_vue', flat=True)))
            page = self.paginate_queryset(request=request, queryset=shop_offers)
            if page is not None:
                serializer = BaseOffersVuesListSerializer(instance=page, many=True)
                return self.get_paginated_response_custom(serializer.data, total_vues=total_vues, auth_shop=auth_shop)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class ShopOfferSolderView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        offer_pk = kwargs.get('offer_pk')
        # # Temp offers
        # if user.is_anonymous:
        #     unique_id = kwargs.get('unique_id')
        #     try:
        #         solder = TempSolder.objects.get(offer=offer_pk, offer__auth_shop__unique_id=unique_id)
        #         offer_details_serializer = BaseTempShopOfferSolderSerializer(solder)
        #         return Response(offer_details_serializer.data, status=status.HTTP_200_OK)
        #     except TempSolder.DoesNotExist:
        #         errors = {"error": ["Offer solder not found."]}
        #         raise ValidationError(errors)
        # # Real offers
        # else:
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
        # # Temp offers
        # if user.is_anonymous:
        #     unique_id = kwargs.get('unique_id')
        #     try:
        #         offer = TempOffers.objects.get(pk=offer_pk, auth_shop__unique_id=unique_id)
        #         if solder_type == 'F':
        #             if float(solder_value) >= offer.price:
        #                 errors = {"error": ["Solder fix price is more than the offer price."]}
        #                 raise ValidationError(errors)
        #         if solder_type == 'P':
        #             if float(solder_value) >= 100:
        #                 errors = {"error": ["Solder can't be applied up to 100%."]}
        #                 raise ValidationError(errors)
        #         serializer = BaseTempShopOfferSolderSerializer(data={
        #             'offer': offer.pk,
        #             'solder_type': solder_type,
        #             'solder_value': float(solder_value),
        #         })
        #         if serializer.is_valid():
        #             serializer.save()
        #             return Response(data=serializer.data, status=status.HTTP_200_OK)
        #         raise ValidationError(serializer.errors)
        #     except TempOffers.DoesNotExist:
        #         errors = {"error": ["Offer not found."]}
        #         raise ValidationError(errors)
        # # Real offers
        # else:
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
        # # Temp offers
        # if user.is_anonymous:
        #     unique_id = kwargs.get('unique_id')
        #     try:
        #         solder = TempSolder.objects.get(offer=offer_pk, offer__auth_shop__unique_id=unique_id)
        #         if solder.solder_type == 'F':
        #             if solder.solder_value >= solder.offer.price:
        #                 errors = {"error": ["Solder fix price is more than the offer price."]}
        #                 raise ValidationError(errors)
        #         if solder.solder_type == 'P':
        #             if solder.solder_value >= 100:
        #                 errors = {"error": ["Solder can't be applied up to 100%."]}
        #                 raise ValidationError(errors)
        #         serializer = BaseTempShopOfferSolderPutSerializer(solder, data=request.data, partial=True)
        #         if serializer.is_valid():
        #             serializer.save()
        #             data = {
        #                 'offer': int(offer_pk),
        #                 'solder_type': serializer.data.get('solder_type'),
        #                 'solder_value': serializer.data.get('solder_value'),
        #             }
        #             return Response(data=data, status=status.HTTP_200_OK)
        #         raise ValidationError(serializer.errors)
        #     except TempSolder.DoesNotExist:
        #         errors = {"error": ["Solder not found."]}
        #         raise ValidationError(errors)
        # # Real offers
        # else:
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
        # # Temp offers
        # if user.is_anonymous:
        #     unique_id = kwargs.get('unique_id')
        #     try:
        #         TempSolder.objects.get(offer=offer_pk, offer__auth_shop__unique_id=unique_id).delete()
        #         return Response(status=status.HTTP_204_NO_CONTENT)
        #     except TempSolder.DoesNotExist:
        #         errors = {"error": ["Solder not found."]}
        #         raise ValidationError(errors)
        # # Real offers
        # else:
        try:
            Solder.objects.get(offer=offer_pk, offer__auth_shop__user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Solder.DoesNotExist:
            errors = {"error": ["Solder not found."]}
            raise ValidationError(errors)


# TODO : duplicate missing all_cities
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
                'picture_4': offer.picture_4 if offer.picture_4 else None,
                'picture_1_thumbnail': offer.picture_1_thumbnail if offer.picture_1_thumbnail else None,
                'picture_2_thumbnail': offer.picture_2_thumbnail if offer.picture_2_thumbnail else None,
                'picture_3_thumbnail': offer.picture_3_thumbnail if offer.picture_3_thumbnail else None,
                'picture_4_thumbnail': offer.picture_4_thumbnail if offer.picture_4_thumbnail else None,
                'description': description,
                'price': price
            })
            if offer_serializer.is_valid():
                # Duplicate offer
                offer_serializer = offer_serializer.save()
                # Duplicate pictures
                base_duplicate_offer_images.apply_async((offer.pk, offer_serializer.pk,), )
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
                    'picture_4': offer_serializer.get_absolute_picture_4_img,
                    'picture_4_thumb': offer_serializer.get_absolute_picture_4_thumbnail,
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


# class GetLastThreeDeliveriesView(APIView):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     @staticmethod
#     def get(request, *args, **kwargs):
#         user = request.user
#         # # Temp offers
#         # if user.is_anonymous:
#         #     unique_id = kwargs.get('unique_id')
#         #     try:
#         #         auth_shop = TempShop.objects.get(unique_id=unique_id)
#         #         offers = TempOffers.objects \
#         #             .select_related('temp_offer_products') \
#         #             .prefetch_related('temp_offer_delivery') \
#         #             .filter(auth_shop=auth_shop).order_by('-created_date')
#         #         data = defaultdict(list)
#         #         for offer in offers:
#         #             deliveries = offer.temp_offer_delivery.all().order_by('-pk')
#         #             for delivery in deliveries:
#         #                 delivery_cities = delivery.delivery_city.all().values('pk', name_=F('name_fr'))
#         #                 delivery_city = []
#         #                 for i in delivery_cities:
#         #                     delivery_obj = {'pk': '', 'name': ''}
#         #                     for k, v in i.items():
#         #                         if k == 'name_':
#         #                             delivery_obj['name'] = v
#         #                         else:
#         #                             delivery_obj[k] = v
#         #                     delivery_city.append(delivery_obj)
#         #                 deliveries_list = {
#         #                     'pk': '',
#         #                     'delivery_city': '',
#         #                     'all_cities': False,
#         #                     'delivery_price': '',
#         #                     'delivery_days': '',
#         #                 }
#         #                 dict_title = "deliveries"
#         #                 deliveries_list['pk'] = delivery.pk
#         #                 deliveries_list['delivery_city'] = delivery_city
#         #                 deliveries_list['all_cities'] = delivery.all_cities
#         #                 deliveries_list['delivery_price'] = delivery.delivery_price
#         #                 deliveries_list['delivery_days'] = delivery.delivery_days
#         #                 data[dict_title].append(deliveries_list)
#         #                 if len(data['deliveries']) == 3:
#         #                     break
#         #             if len(data['deliveries']) == 3:
#         #                 break
#         #         return Response(data, status=status.HTTP_200_OK)
#         #     except TempShop.DoesNotExist:
#         #         errors = {"error": ["Shop not found."]}
#         #         raise ValidationError(errors)
#         # # Real offers
#         # else:
#         try:
#             auth_shop = AuthShop.objects.get(user=user)
#             offers = Offers.objects \
#                 .select_related('offer_products') \
#                 .prefetch_related('offer_delivery') \
#                 .filter(auth_shop=auth_shop).order_by('-created_date')
#             data = defaultdict(list)
#             for offer in offers:
#                 deliveries = offer.offer_delivery.all().order_by('-pk')
#                 for delivery in deliveries:
#                     delivery_cities = delivery.delivery_city.all().values('pk', name_=F('name_fr'))
#                     delivery_city = []
#                     for i in delivery_cities:
#                         delivery_obj = {'pk': '', 'name': ''}
#                         for k, v in i.items():
#                             if k == 'name_':
#                                 delivery_obj['name'] = v
#                             else:
#                                 delivery_obj[k] = v
#                         delivery_city.append(delivery_obj)
#                     deliveries_list = {
#                         'pk': '',
#                         'delivery_city': '',
#                         'all_cities': False,
#                         'delivery_price': '',
#                         'delivery_days': '',
#                     }
#                     dict_title = "deliveries"
#                     deliveries_list['pk'] = delivery.pk
#                     deliveries_list['delivery_city'] = delivery_city
#                     deliveries_list['all_cities'] = delivery.all_cities
#                     deliveries_list['delivery_price'] = delivery.delivery_price
#                     deliveries_list['delivery_days'] = delivery.delivery_days
#                     data[dict_title].append(deliveries_list)
#                     if len(data['deliveries']) == 3:
#                         break
#                 if len(data['deliveries']) == 3:
#                     break
#             return Response(data, status=status.HTTP_200_OK)
#         except AuthShop.DoesNotExist:
#             errors = {"error": ["Shop not found."]}
#             raise ValidationError(errors)


class GetLastThreeDeliveriesViewV2(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        # # Temp offers
        # if user.is_anonymous:
        #     unique_id = kwargs.get('unique_id')
        #     try:
        #         auth_shop = TempShop.objects.get(unique_id=unique_id)
        #         offers = TempOffers.objects \
        #             .select_related('temp_offer_products') \
        #             .prefetch_related('temp_offer_delivery') \
        #             .filter(auth_shop=auth_shop).order_by('-created_date')
        #         data = defaultdict(list)
        #         result_deliveries = {
        #             'delivery_city_1': '',
        #             'all_cities_1': False,
        #             'delivery_price_1': '',
        #             'delivery_days_1': '',
        #             'delivery_city_2': '',
        #             'all_cities_2': False,
        #             'delivery_price_2': '',
        #             'delivery_days_2': '',
        #             'delivery_city_3': '',
        #             'all_cities_3': False,
        #             'delivery_price_3': '',
        #             'delivery_days_3': '',
        #         }
        #         for offer in offers:
        #             deliveries = offer.temp_offer_delivery.all().order_by('-pk')
        #             for delivery in deliveries:
        #                 single_delivery = {'delivery_city': delivery.delivery_city.all().values_
        #                 list('name_fr', flat=True),
        #                                    'all_cities': delivery.all_cities,
        #                                    'delivery_price': delivery.delivery_price,
        #                                    'delivery_days': delivery.delivery_days}
        #                 data["deliveries"].append(single_delivery)
        #
        #                 # delivery_cities = delivery.delivery_city.all().values('pk', name_=F('name_fr'))
        #                 # delivery_city = []
        #                 # for i in delivery_cities:
        #                 #     delivery_obj = {'pk': '', 'name': ''}
        #                 #     for k, v in i.items():
        #                 #         if k == 'name_':
        #                 #             delivery_obj['name'] = v
        #                 #         else:
        #                 #             delivery_obj[k] = v
        #                 #     delivery_city.append(delivery_obj)
        #                 # deliveries_list = {
        #                 #     'pk': '',
        #                 #     'delivery_city': '',
        #                 #     'all_cities': False,
        #                 #     'delivery_price': '',
        #                 #     'delivery_days': '',
        #                 # }
        #                 # dict_title = "deliveries"
        #                 # deliveries_list['pk'] = delivery.pk
        #                 # deliveries_list['delivery_city'] = delivery_city
        #                 # deliveries_list['all_cities'] = delivery.all_cities
        #                 # deliveries_list['delivery_price'] = delivery.delivery_price
        #                 # deliveries_list['delivery_days'] = delivery.delivery_days
        #                 # data[dict_title].append(deliveries_list)
        #                 if len(data['deliveries']) == 3:
        #                     break
        #             if len(data['deliveries']) == 3:
        #                 for count, final_delivery in enumerate(data['deliveries']):
        #                     if count == 0:
        #                         result_deliveries['delivery_city_1'] = ','.join(final_delivery.get('delivery_city'))
        #                         result_deliveries['all_cities_1'] = final_delivery.get('all_cities')
        #                         result_deliveries['delivery_days_1'] = final_delivery.get('delivery_days')
        #                         result_deliveries['delivery_price_1'] = final_delivery.get('delivery_price')
        #                         continue
        #                     elif count == 1:
        #                         if result_deliveries['delivery_city_1'] == ','.join(final_delivery
        #                                                                                     .get('delivery_city')):
        #                             continue
        #                         result_deliveries['delivery_city_2'] = ','.join(final_delivery.get('delivery_city'))
        #                         result_deliveries['all_cities_2'] = final_delivery.get('all_cities')
        #                         result_deliveries['delivery_days_2'] = final_delivery.get('delivery_days')
        #                         result_deliveries['delivery_price_2'] = final_delivery.get('delivery_price')
        #                         continue
        #                     elif count == 2:
        #                         if (result_deliveries['delivery_city_1'] or result_deliveries['delivery_city_2']) \
        #                                 == ','.join(final_delivery.get('delivery_city')):
        #                             continue
        #                         result_deliveries['delivery_city_3'] = ','.join(final_delivery.get('delivery_city'))
        #                         result_deliveries['all_cities_3'] = final_delivery.get('all_cities')
        #                         result_deliveries['delivery_days_3'] = final_delivery.get('delivery_days')
        #                         result_deliveries['delivery_price_3'] = final_delivery.get('delivery_price')
        #                         continue
        #                 break
        #         return Response(result_deliveries, status=status.HTTP_200_OK)
        #     except TempShop.DoesNotExist:
        #         errors = {"error": ["Shop not found."]}
        #         raise ValidationError(errors)
        # # Real offers
        # else:
        try:
            auth_shop = AuthShop.objects.get(user=user)
            offers = Offers.objects \
                .select_related('offer_products') \
                .prefetch_related('offer_delivery') \
                .filter(auth_shop=auth_shop).order_by('-created_date')
            data = defaultdict(list)
            result_deliveries = {
                'delivery_city_1': '',
                'all_cities_1': False,
                'delivery_price_1': '',
                'delivery_days_1': '',
                'delivery_city_2': '',
                'all_cities_2': False,
                'delivery_price_2': '',
                'delivery_days_2': '',
                'delivery_city_3': '',
                'all_cities_3': False,
                'delivery_price_3': '',
                'delivery_days_3': '',
            }
            for offer in offers:
                deliveries = offer.offer_delivery.all().order_by('-pk')
                for delivery in deliveries:
                    single_delivery = {
                        'delivery_city': delivery.delivery_city.all().values_list('name_fr', flat=True),
                        'all_cities': delivery.all_cities,
                        'delivery_price': delivery.delivery_price,
                        'delivery_days': delivery.delivery_days}
                    data["deliveries"].append(single_delivery)
                    if len(data['deliveries']) == 3:
                        break
                if len(data['deliveries']) == 3:
                    for count, final_delivery in enumerate(data['deliveries']):
                        if count == 0:
                            result_deliveries['delivery_city_1'] = ','.join(final_delivery.get('delivery_city'))
                            result_deliveries['all_cities_1'] = final_delivery.get('all_cities')
                            result_deliveries['delivery_days_1'] = final_delivery.get('delivery_days')
                            result_deliveries['delivery_price_1'] = final_delivery.get('delivery_price')
                            continue
                        elif count == 1:
                            if result_deliveries['delivery_city_1'] == ','.join(final_delivery.get('delivery_city')):
                                continue
                            result_deliveries['delivery_city_2'] = ','.join(final_delivery.get('delivery_city'))
                            result_deliveries['all_cities_2'] = final_delivery.get('all_cities')
                            result_deliveries['delivery_days_2'] = final_delivery.get('delivery_days')
                            result_deliveries['delivery_price_2'] = final_delivery.get('delivery_price')
                            continue
                        elif count == 2:
                            if (result_deliveries['delivery_city_1'] or result_deliveries['delivery_city_2']) \
                                    == ','.join(final_delivery.get('delivery_city')):
                                continue
                            result_deliveries['delivery_city_3'] = ','.join(final_delivery.get('delivery_city'))
                            result_deliveries['all_cities_3'] = final_delivery.get('all_cities')
                            result_deliveries['delivery_days_3'] = final_delivery.get('delivery_days')
                            result_deliveries['delivery_price_3'] = final_delivery.get('delivery_price')
                            continue
                    break
            return Response(result_deliveries, status=status.HTTP_200_OK)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)


class GetLastUsedLocalisationView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        offer_type = kwargs.get('offer_type')
        user = request.user
        # # Temp offers
        # if user.is_anonymous:
        #     unique_id = kwargs.get('unique_id')
        #     try:
        #         auth_shop = TempShop.objects.get(unique_id=unique_id)
        #         offer = TempOffers.objects \
        #             .select_related('temp_offer_products') \
        #             .select_related('temp_offer_services') \
        #             .prefetch_related('temp_offer_delivery') \
        #             .filter(auth_shop=auth_shop).order_by('-created_date').last()
        #         if offer:
        #             data_product = {
        #                 'longitude': None,
        #                 'latitude': None,
        #                 'localisation_name': None,
        #             }
        #             data_service = {
        #                 'zone_by': None,
        #                 'longitude': None,
        #                 'latitude': None,
        #                 'km_radius': None,
        #                 'localisation_name': None,
        #             }
        #             if offer.offer_type == offer_type:
        #                 if offer.temp_offer_products.product_address:
        #                     data_product['longitude'] = offer.temp_offer_products.product_longitude
        #                     data_product['latitude'] = offer.temp_offer_products.product_latitude
        #                     data_product['localisation_name'] = offer.temp_offer_products.product_address
        #                     return Response(data=data_product, status=status.HTTP_200_OK)
        #             elif offer.offer_type == offer_type:
        #                 if offer.temp_offer_services.service_address:
        #                     data_service['zone_by'] = offer.temp_offer_services.service_zone_by
        #                     data_service['longitude'] = offer.temp_offer_services.service_longitude
        #                     data_service['latitude'] = offer.temp_offer_services.service_latitude
        #                     data_service['km_radius'] = offer.temp_offer_services.service_km_radius
        #                     data_service['localisation_name'] = offer.temp_offer_services.service_address
        #                     return Response(data=data_service, status=status.HTTP_200_OK)
        #             return Response(status=status.HTTP_204_NO_CONTENT)
        #         return Response(status=status.HTTP_204_NO_CONTENT)
        #     except TempOffers.DoesNotExist:
        #         errors = {"error": ["Offer not found."]}
        #         raise ValidationError(errors)
        # # Real offers
        # else:
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


class GetServicesAvailabilityDays(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        availability_days = request.data.get('availability_days')
        availability_days_list = str(availability_days).split(',')
        service_days = ServiceDays.objects.filter(code_day__in=availability_days_list)
        result = []
        for service_day in service_days:
            result_obj = {
                'pk': service_day.pk,
                'code_day': service_day.code_day,
                'name_day': service_day.name_day,
            }
            result.append(result_obj)
        return Response(data=result, status=status.HTTP_200_OK)


class GetOfferTagsView(ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = OfferTags.objects.all()
    serializer_class = BaseOfferTagsSerializer
    filterset_class = TagsFilterSet
    pagination_class = None

    # def get_queryset(self):
    #     if not self.request.GET.get('name_tag'):
    #         return self.queryset.model.objects.none()
    #     else:
    #         self.filter_class = TagsFilterSet
    #         self.serializer_class = BaseOfferTagsSerializer
    #         return super().get_queryset()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = []
        for obj in serializer.data:
            for k, v in obj.items():
                data.append(v)
        # return Response({'name_tag': data})
        return Response(data=data, status=status.HTTP_200_OK)
