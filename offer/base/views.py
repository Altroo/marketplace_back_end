from collections import defaultdict
from django.core.exceptions import SuspiciousFileOperation, ObjectDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import IntegrityError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from offer.base.serializers import BaseShopOfferSerializer, \
    BaseShopDeliverySerializer, BaseOfferDetailsSerializer, \
    BaseOffersListSerializer, BaseShopOfferSolderSerializer, \
    BaseShopOfferSolderPutSerializer, BaseShopProductSerializer, \
    BaseShopServiceSerializer, BaseProductPutSerializer, \
    BaseServicePutSerializer, BaseOfferPutSerializer, \
    BaseShopOfferDuplicateSerializer, BaseOfferTagsSerializer
from offer.base.filters import TagsFilterSet
from os import path, remove
from Qaryb_API_new.settings import API_URL
from offer.base.tasks import base_generate_offer_thumbnails, base_duplicate_offer_images
from offer.base.models import AuthShop, Offers, Solder, Products, Services, Delivery, OfferTags, \
    Categories, Colors, Sizes, ForWhom, ServiceDays
from offer.mixins import PaginationMixinBy5
from places.base.models import City


class ShopOfferView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
        except AuthShop.DoesNotExist:
            data = {'errors': ['User shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
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
            'picture_4': request.data.get('picture_4', None),
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
                'picture_4': offer.get_absolute_picture_4_img,
                'picture_4_thumb': offer.get_absolute_picture_4_thumbnail,
                'description': description,
                'price': price
            }
            # Categories
            offer_categories = str(request.data.get('offer_categories')).split(',')
            offer_categories = Categories.objects.filter(code_category__in=offer_categories)
            offer_categories_list = []
            for category in offer_categories:
                offer.offer_categories.add(category.pk)
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
                offer_for_whom_list.append(
                    {
                        "pk": for_who.pk,
                        "code_for_whom": for_who.code_for_whom,
                        "name_for_whom": for_who.name_for_whom
                    }
                )
            data['for_whom'] = offer_for_whom_list
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
                tags_list.append(
                    {
                        "pk": tag.pk,
                        "name_tag": tag.name_tag,
                    }
                )
            data['tags'] = tags_list
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
                # # deliveries
                # delivery_city_1 = request.data.get('delivery_city_1')
                # delivery_price_1 = request.data.get('delivery_price_1', None)
                # delivery_days_1 = request.data.get('delivery_days_1', None)
                # delivery_city_2 = request.data.get('delivery_city_2', None)
                # delivery_price_2 = request.data.get('delivery_price_2', None)
                # delivery_days_2 = request.data.get('delivery_days_2', None)
                # delivery_city_3 = request.data.get('delivery_city_3', None)
                # delivery_price_3 = request.data.get('delivery_price_3', None)
                # delivery_days_3 = request.data.get('delivery_days_3', None)
                #
                # delivery_serializer = BaseShopDeliverySerializer(data={
                #     'offer': offer_pk,
                #     'delivery_city_1': delivery_city_1,
                #     'delivery_price_1': delivery_price_1,
                #     'delivery_days_1': delivery_days_1,
                #     'delivery_city_2': delivery_city_2,
                #     'delivery_price_2': delivery_price_2,
                #     'delivery_days_2': delivery_days_2,
                #     'delivery_city_3': delivery_city_3,
                #     'delivery_price_3': delivery_price_3,
                #     'delivery_days_3': delivery_days_3,
                # })
                # if delivery_serializer.is_valid():
                #     delivery_serializer.save()
                #
                #     def removekey(d, key):
                #         r = dict(d)
                #         del r[key]
                #         return r
                #
                #     delivery = removekey(delivery_serializer.data, 'offer')
                #     data['deliveries'] = delivery
                #     # For products
                #     return Response(data=data, status=status.HTTP_200_OK)
                # else:
                #     return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
                if delivery_city_1:
                    cities_str = str(delivery_city_1).split(',')
                    cities = []
                    for city in cities_str:
                        cities.append(int(city))

                    cities = City.objects.filter(pk__in=cities)
                    delivery_cities_1 = []
                    for city in cities:
                        delivery_cities_1.append(
                            {
                                "pk": city.pk,
                                "city_en": city.name_en,
                                "city_fr": city.name_fr,
                                "city_ar": city.name_ar
                            }
                        )
                        delivery_cities_1_pk.append(
                            city.pk
                        )

                # Delivery 2 cities
                delivery_city_2 = request.data.get('delivery_city_2')
                delivery_cities_2_pk = []
                if delivery_city_2:
                    cities_str = str(delivery_city_2).split(',')
                    cities = []
                    for city in cities_str:
                        cities.append(int(city))

                    cities = City.objects.filter(pk__in=cities)
                    delivery_cities_2 = []
                    for city in cities:
                        delivery_cities_2.append(
                            {
                                "pk": city.pk,
                                "city_en": city.name_en,
                                "city_fr": city.name_fr,
                                "city_ar": city.name_ar
                            }
                        )
                        delivery_cities_2_pk.append(
                            city.pk
                        )

                # Delivery 3 cities
                delivery_city_3 = request.data.get('delivery_city_3')
                delivery_cities_3_pk = []
                if delivery_city_3:
                    cities_str = str(delivery_city_3).split(',')
                    cities = []
                    for city in cities_str:
                        cities.append(int(city))

                    cities = City.objects.filter(pk__in=cities)
                    delivery_cities_3 = []
                    for city in cities:
                        delivery_cities_3.append(
                            {
                                "pk": city.pk,
                                "city_en": city.name_en,
                                "city_fr": city.name_fr,
                                "city_ar": city.name_ar
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
                            'offer': offer_pk,
                            'delivery_city': delivery_cities_1_pk,
                            'delivery_price': float(delivery_price_1),
                            'delivery_days': int(delivery_days_1)
                        }
                    )
                if delivery_city_2:
                    city_2_check = True
                    deliveries.append(
                        {
                            'offer': offer_pk,
                            'delivery_city': delivery_cities_2_pk,
                            'delivery_price': float(delivery_price_2),
                            'delivery_days': int(delivery_days_2)
                        }
                    )
                if delivery_city_3:
                    city_3_check = True
                    deliveries.append(
                        {
                            'offer': offer_pk,
                            'delivery_city': delivery_cities_3_pk,
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
                    # For products
                    return Response(data=data, status=status.HTTP_200_OK)
                else:
                    return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                offer.delete()
                if offer_type == 'V' and product_serializer_errors:
                    return Response(product_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
                if offer_type == 'S' and service_serializer_errors:
                    return Response(service_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(offer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        offer_pk = request.data.get('offer_id')
        try:
            offer = Offers.objects.get(pk=offer_pk)
            offer_pk = offer.pk
            picture_1 = request.data.get('picture_1', None)
            picture_2 = request.data.get('picture_2', None)
            picture_3 = request.data.get('picture_3', None)
            picture_4 = request.data.get('picture_4', None)

            previous_images = list()
            previous_images.append(API_URL + offer.picture_1.url
                                   if offer.picture_1 else False)
            previous_images.append(API_URL + offer.picture_2.url
                                   if offer.picture_2 else False)
            previous_images.append(API_URL + offer.picture_3.url
                                   if offer.picture_3 else False)
            previous_images.append(API_URL + offer.picture_4.url
                                   if offer.picture_4 else False)

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
                        elif img_1_index == 2:
                            picture_1 = offer.picture_3
                        else:
                            picture_1 = offer.picture_4
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
                            picture_2 = offer.picture_2
                        elif img_2_index == 1:
                            picture_2 = offer.picture_2
                        elif img_2_index == 2:
                            picture_2 = offer.picture_2
                        else:
                            picture_2 = offer.picture_2
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
                            picture_3 = offer.picture_3
                        elif img_3_index == 1:
                            picture_3 = offer.picture_3
                        elif img_3_index == 2:
                            picture_3 = offer.picture_3
                        else:
                            picture_3 = offer.picture_3
                    # None wasn't sent
                    except ValueError:
                        picture_3 = None

            if isinstance(picture_4, InMemoryUploadedFile):
                try:
                    picture_4_path = self.parent_file_dir + offer.picture_4.url
                    picture_4_thumb_path = self.parent_file_dir + offer.picture_4_thumbnail.url
                    remove(picture_4_path)
                    remove(picture_4_thumb_path)
                except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                    pass
                offer.picture_4 = None
                offer.save()
            else:
                # src
                if picture_4 in previous_images:
                    try:
                        img_4_index = previous_images.index(picture_4)
                        if img_4_index == 0:
                            picture_4 = offer.picture_4
                        elif img_4_index == 1:
                            picture_4 = offer.picture_4
                        elif img_4_index == 2:
                            picture_4 = offer.picture_4
                        else:
                            picture_4 = offer.picture_4
                    # None wasn't sent
                    except ValueError:
                        picture_4 = None

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
                'picture_4': picture_4,
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
                        'picture_4': updated_offer.get_absolute_picture_4_img,
                        'picture_4_thumb': updated_offer.get_absolute_picture_4_thumbnail,
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
                        # # UPDATE DELIVERIES
                        # delivery_city_1 = request.data.get('delivery_city_1', None)
                        # delivery_price_1 = request.data.get('delivery_price_1', None)
                        # delivery_days_1 = request.data.get('delivery_days_1', None)
                        # delivery_city_2 = request.data.get('delivery_city_2', None)
                        # delivery_price_2 = request.data.get('delivery_price_2', None)
                        # delivery_days_2 = request.data.get('delivery_days_2', None)
                        # delivery_city_3 = request.data.get('delivery_city_3', None)
                        # delivery_price_3 = request.data.get('delivery_price_3', None)
                        # delivery_days_3 = request.data.get('delivery_days_3', None)
                        #
                        # delivery_serializer = BaseShopDeliveryPUTSerializer(data={
                        #     'offer': offer_pk,
                        #     'delivery_city_1': delivery_city_1,
                        #     'delivery_price_1': delivery_price_1,
                        #     'delivery_days_1': delivery_days_1,
                        #     'delivery_city_2': delivery_city_2,
                        #     'delivery_price_2': delivery_price_2,
                        #     'delivery_days_2': delivery_days_2,
                        #     'delivery_city_3': delivery_city_3,
                        #     'delivery_price_3': delivery_price_3,
                        #     'delivery_days_3': delivery_days_3,
                        # })
                        # if delivery_serializer.is_valid():
                        #     delivery = Delivery.objects.get(offer=offer_pk)
                        #     delivery_serializer.update(delivery, delivery_serializer.validated_data)
                        #     data['deliveries'] = delivery_serializer.data
                        #     return Response(data, status=status.HTTP_200_OK)
                        # else:
                        #     return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
                        if delivery_city_1:
                            cities_str = str(delivery_city_1).split(',')
                            cities = []
                            for city in cities_str:
                                cities.append(int(city))

                            cities = City.objects.filter(pk__in=cities)
                            delivery_cities_1 = []
                            for city in cities:
                                delivery_cities_1.append(
                                    {
                                        "pk": city.pk,
                                        "city_en": city.name_en,
                                        "city_fr": city.name_fr,
                                        "city_ar": city.name_ar
                                    }
                                )
                                delivery_cities_1_pk.append(
                                    city.pk
                                )

                        # Delivery 2 cities
                        delivery_city_2 = request.data.get('delivery_city_2')
                        delivery_cities_2_pk = []
                        if delivery_city_2:
                            cities_str = str(delivery_city_2).split(',')
                            cities = []
                            for city in cities_str:
                                cities.append(int(city))

                            cities = City.objects.filter(pk__in=cities)
                            delivery_cities_2 = []
                            for city in cities:
                                delivery_cities_2.append(
                                    {
                                        "pk": city.pk,
                                        "city_en": city.name_en,
                                        "city_fr": city.name_fr,
                                        "city_ar": city.name_ar
                                    }
                                )
                                delivery_cities_2_pk.append(
                                    city.pk
                                )

                        # Delivery 3 cities
                        delivery_city_3 = request.data.get('delivery_city_3')
                        delivery_cities_3_pk = []
                        if delivery_city_3:
                            cities_str = str(delivery_city_3).split(',')
                            cities = []
                            for city in cities_str:
                                cities.append(int(city))

                            cities = City.objects.filter(pk__in=cities)
                            delivery_cities_3 = []
                            for city in cities:
                                delivery_cities_3.append(
                                    {
                                        "pk": city.pk,
                                        "city_en": city.name_en,
                                        "city_fr": city.name_fr,
                                        "city_ar": city.name_ar
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
                                    'offer': offer_pk,
                                    'delivery_city': delivery_cities_1_pk,
                                    'delivery_price': float(delivery_price_1),
                                    'delivery_days': int(delivery_days_1)
                                }
                            )
                        if delivery_city_2:
                            city_2_check = True
                            deliveries.append(
                                {
                                    'offer': offer_pk,
                                    'delivery_city': delivery_cities_2_pk,
                                    'delivery_price': float(delivery_price_2),
                                    'delivery_days': int(delivery_days_2)
                                }
                            )
                        if delivery_city_3:
                            city_3_check = True
                            deliveries.append(
                                {
                                    'offer': offer_pk,
                                    'delivery_city': delivery_cities_3_pk,
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
                            data['deliveries'] = deliveries
                            return Response(data, status=status.HTTP_200_OK)
                        else:
                            return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
                        return Response(product_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
                    if offer_type == 'S' and service_serializer_errors:
                        return Response(service_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(offer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Offers.DoesNotExist:
            data = {'errors': [' offer not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        offer_pk = request.data.get('offer_id')
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
        except AuthShop.DoesNotExist:
            data = {'errors': ['User shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
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
            data = {'errors': ['Offer not yours to delete.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetOneOfferView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        offer_id = kwargs.get('offer_id')
        try:
            offer = Offers.objects \
                .select_related('offer_solder') \
                .select_related('offer_products') \
                .select_related('offer_services') \
                .prefetch_related('offer_delivery') \
                .get(pk=offer_id)
            offer_details_serializer = BaseOfferDetailsSerializer(offer)
            return Response(offer_details_serializer.data, status=status.HTTP_200_OK)
        except Offers.DoesNotExist:
            data = {'errors': ['Offer not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetShopOffersListView(APIView, PaginationMixinBy5):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            shop = AuthShop.objects.get(user=user)
            shop_offers = Offers.objects \
                .select_related('offer_solder') \
                .select_related('offer_products') \
                .select_related('offer_services') \
                .prefetch_related('offer_delivery') \
                .filter(shop=shop).order_by('-created_date')
            page = self.paginate_queryset(queryset=shop_offers)
            if page is not None:
                serializer = BaseOffersListSerializer(instance=page, many=True)
                return self.get_paginated_response(serializer.data)
            data = {'response': 'Shop has no products.'}
            return Response(data=data, status=status.HTTP_200_OK)
        except AuthShop.DoesNotExist:
            data = {'errors': ['User shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopOfferSolderView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        offer_id = kwargs.get('offer_id')
        try:
            solder = Solder.objects.get(offer=offer_id)
            offer_details_serializer = BaseShopOfferSolderSerializer(solder)
            return Response(offer_details_serializer.data, status=status.HTTP_200_OK)
        except Solder.DoesNotExist:
            data = {'errors': ['Offer solder not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def post(request, *args, **kwargs):
        offer_id = request.data.get('offer_id')
        offer = Offers.objects.get(pk=offer_id).pk
        serializer = BaseShopOfferSolderSerializer(data={
            'offer': offer,
            'solder_type': request.data.get('solder_type'),
            'solder_value': request.data.get('solder_value'),
        })
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(request, *args, **kwargs):
        offer_id = request.data.get('offer_id')
        solder = Solder.objects.get(offer=offer_id)
        serializer = BaseShopOfferSolderPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(solder, serializer.validated_data)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        data = {}
        offer_id = request.data.get('offer_id')
        try:
            Solder.objects.get(offer=offer_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Solder.DoesNotExist:
            data['errors'] = ["Offer solder not found."]
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class ShopOfferDuplicateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def post(request, *args, **kwargs):
        offer_id = request.data.get('offer_id')
        offer = Offers.objects \
            .select_related('offer_solder') \
            .select_related('offer_products') \
            .select_related('offer_services') \
            .prefetch_related('offer_delivery') \
            .get(pk=offer_id)
        # Title
        title = offer.title
        # Description
        description = offer.description
        # Price
        price = offer.price
        # Offer type
        offer_type = offer.offer_type
        offer_serializer = BaseShopOfferDuplicateSerializer(data={
            'shop': offer.shop.pk,
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
            base_duplicate_offer_images.apply_async(args=(offer.pk, offer_serializer.pk, 'Offers'), )
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
                # delivery_city_1 = request.data.get('delivery_city_1')
                # delivery_price_1 = request.data.get('delivery_price_1', None)
                # delivery_days_1 = request.data.get('delivery_days_1', None)
                # delivery_city_2 = request.data.get('delivery_city_2', None)
                # delivery_price_2 = request.data.get('delivery_price_2', None)
                # delivery_days_2 = request.data.get('delivery_days_2', None)
                # delivery_city_3 = request.data.get('delivery_city_3', None)
                # delivery_price_3 = request.data.get('delivery_price_3', None)
                # delivery_days_3 = request.data.get('delivery_days_3', None)
                #
                # delivery_serializer = BaseShopDeliverySerializer(data={
                #     'offer': offer.pk,
                #     'delivery_city_1': delivery_city_1,
                #     'delivery_price_1': delivery_price_1,
                #     'delivery_days_1': delivery_days_1,
                #     'delivery_city_2': delivery_city_2,
                #     'delivery_price_2': delivery_price_2,
                #     'delivery_days_2': delivery_days_2,
                #     'delivery_city_3': delivery_city_3,
                #     'delivery_price_3': delivery_price_3,
                #     'delivery_days_3': delivery_days_3,
                # })
                # if delivery_serializer.is_valid():
                #     delivery_serializer.save()
                #
                #     def removekey(d, key):
                #         r = dict(d)
                #         del r[key]
                #         return r
                #
                #     delivery = removekey(delivery_serializer.data, 'offer')
                #     data['deliveries'] = delivery
                #     # For products
                #     return Response(data=data, status=status.HTTP_200_OK)
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
                if delivery_city_1:
                    cities = City.objects.filter(pk__in=delivery_city_1)
                    delivery_cities_1 = []
                    for city in cities:
                        delivery_cities_1.append(
                            {
                                "pk": city.pk,
                                "city_en": city.name_en,
                                "city_fr": city.name_fr,
                                "city_ar": city.name_ar
                            }
                        )
                        delivery_cities_1_pk.append(
                            city.pk
                        )
                # Delivery 2 cities
                delivery_cities_2_pk = []
                if delivery_city_2:
                    cities = City.objects.filter(pk__in=delivery_city_2)
                    delivery_cities_2 = []
                    for city in cities:
                        delivery_cities_2.append(
                            {
                                "pk": city.pk,
                                "city_en": city.name_en,
                                "city_fr": city.name_fr,
                                "city_ar": city.name_ar
                            }
                        )
                        delivery_cities_2_pk.append(
                            city.pk
                        )
                # Delivery 3 cities
                delivery_cities_3_pk = []
                if delivery_city_3:
                    cities = City.objects.filter(pk__in=delivery_city_3)
                    delivery_cities_3 = []
                    for city in cities:
                        delivery_cities_3.append(
                            {
                                "pk": city.pk,
                                "city_en": city.name_en,
                                "city_fr": city.name_fr,
                                "city_ar": city.name_ar
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
                            'offer': offer_serializer.pk,
                            'delivery_city': delivery_cities_1_pk,
                            'delivery_price': float(delivery_price_1),
                            'delivery_days': int(delivery_days_1)
                        }
                    )
                if delivery_city_2:
                    city_2_check = True
                    deliveries.append(
                        {
                            'offer': offer_serializer.pk,
                            'delivery_city': delivery_cities_2_pk,
                            'delivery_price': float(delivery_price_2),
                            'delivery_days': int(delivery_days_2)
                        }
                    )
                if delivery_city_3:
                    city_3_check = True
                    deliveries.append(
                        {
                            'offer': offer_serializer.pk,
                            'delivery_city': delivery_cities_3_pk,
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
                    return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                offer_serializer.delete()
                if offer_type == 'V' and product_serializer_errors:
                    return Response(product_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
                if offer_type == 'S' and service_serializer_errors:
                    return Response(service_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(offer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetLastThreeDeliveriesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    # @staticmethod
    # def get(request, *args, **kwargs):
    #     auth_shop_pk = kwargs.get('auth_shop_pk')
    #     try:
    #         auth_shop = AuthShop.objects.get(pk=auth_shop_pk)
    #         offers = Offers.objects \
    #             .select_related('offer_products') \
    #             .prefetch_related('offer_delivery') \
    #             .filter(auth_shop=auth_shop).order_by('-created_date')
    #         data = {
    #             'delivery_city_1': None,
    #             'delivery_price_1': None,
    #             'delivery_days_1': None,
    #             'delivery_city_2': None,
    #             'delivery_price_2': None,
    #             'delivery_days_2': None,
    #             'delivery_city_3': None,
    #             'delivery_price_3': None,
    #             'delivery_days_3': None
    #         }
    #         delivery_1 = False
    #         delivery_2 = False
    #         delivery_3 = False
    #         for offer in offers:
    #             if not delivery_1:
    #                 if offer.offer_delivery.delivery_city_1:
    #                     data['delivery_city_1'] = offer.offer_delivery.delivery_city_1
    #                     data['delivery_price_1'] = offer.offer_delivery.delivery_price_1
    #                     data['delivery_days_1'] = offer.offer_delivery.delivery_days_1
    #                     delivery_1 = True
    #             if not delivery_2:
    #                 if offer.offer_delivery.delivery_city_2:
    #                     data['delivery_city_2'] = offer.offer_delivery.delivery_city_2
    #                     data['delivery_price_2'] = offer.offer_delivery.delivery_price_2
    #                     data['delivery_days_2'] = offer.offer_delivery.delivery_days_2
    #                     delivery_2 = True
    #             if not delivery_3:
    #                 if offer.offer_delivery.delivery_city_3:
    #                     data['delivery_city_3'] = offer.offer_delivery.delivery_city_3
    #                     data['delivery_price_3'] = offer.offer_delivery.delivery_price_3
    #                     data['delivery_days_3'] = offer.offer_delivery.delivery_days_3
    #                     delivery_3 = True
    #         return Response(data=data, status=status.HTTP_200_OK)
    #     except AuthShop.DoesNotExist:
    #         data = {'errors': ['Auth shop not found.']}
    #         return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
    @staticmethod
    def get(request, *args, **kwargs):
        auth_shop_pk = kwargs.get('auth_shop_pk')
        try:
            auth_shop = AuthShop.objects.get(pk=auth_shop_pk)
            offers = Offers.objects \
                .select_related('offer_products') \
                .prefetch_related('offer_delivery') \
                .filter(auth_shop=auth_shop).order_by('-created_date')
            data = defaultdict(list)
            for offer in offers:
                deliveries = offer.offer_delivery.all().order_by('-pk')
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
                        .values_list('name_en', flat=True)
                    deliveries_list['delivery_price'] = delivery.delivery_price
                    deliveries_list['delivery_days'] = delivery.delivery_days
                    data[dict_title].append(deliveries_list)
                    if len(data['deliveries']) == 3:
                        break
                if len(data['deliveries']) == 3:
                    break
            return Response(data, status=status.HTTP_200_OK)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetLastUsedLocalisationView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        offer_type = kwargs.get('offer_type')
        try:
            auth_shop = AuthShop.objects.get(unique_id=unique_id)
            offer = Offers.objects \
                .select_related('offer_products') \
                .select_related('offer_services') \
                .prefetch_related('offer_delivery') \
                .filter(auth_shop=auth_shop).order_by('-created_date').last()
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
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetTagsView(ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = OfferTags.objects.all()
    serializer_class = BaseOfferTagsSerializer
    filter_class = TagsFilterSet
    pagination_class = None
