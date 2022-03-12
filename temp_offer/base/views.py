from django.core.exceptions import SuspiciousFileOperation, ObjectDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from temp_offer.base.serializers import BaseTempShopOfferSerializer, \
    BaseTempShopDeliverySerializer, BaseTempOfferDetailsSerializer, \
    BaseTempOfferssListSerializer, BaseTempShopOfferSolderSerializer, \
    BaseTempShopOfferSolderPutSerializer, BaseTempShopProductSerializer, \
    BaseTempShopServiceSerializer, BaseTempProductPutSerializer, \
    BaseTempServicePutSerializer, BaseTempOfferPutSerializer, \
    BaseTempShopOfferDuplicateSerializer
from os import path, remove
from Qaryb_API_new.settings import API_URL
from offer.base.tasks import base_generate_offer_thumbnails, base_duplicate_offer_images
from temp_offer.base.models import TempShop, TempOffers, TempSolder, TempProducts, TempServices, TempDelivery
from offer.base.models import Categories, Colors, Sizes, ForWhom, ServiceDays
from offer.mixins import PaginationMixinBy5
from places.base.models import City
from collections import defaultdict


class TempShopOfferView(APIView):
    permission_classes = (permissions.AllowAny,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def post(request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        try:
            temp_shop = TempShop.objects.get(unique_id=unique_id)
        except TempShop.DoesNotExist:
            data = {'errors': ['Temp offer not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        offer_type = request.data.get('offer_type')
        title = request.data.get('title')
        description = request.data.get('description')
        price = request.data.get('price')
        offer_serializer = BaseTempShopOfferSerializer(data={
            'temp_shop': temp_shop.pk,
            'offer_type': offer_type,
            'title': title,
            'picture_1': request.data.get('picture_1', None),
            'picture_2': request.data.get('picture_2', None),
            'picture_3': request.data.get('picture_3', None),
            'picture_4': request.data.get('picture_4', None),
            'description': description,
            'price': price,
        })
        if offer_serializer.is_valid():
            product_valid = False
            product_serializer_errors = None
            service_serializer_errors = None
            temp_offer = offer_serializer.save()
            temp_offer_pk = temp_offer.pk
            # Generate thumbnails
            base_generate_offer_thumbnails.apply_async((temp_offer_pk, 'TempOffers'), )
            data = {
                'pk': temp_offer_pk,
                'offer_type': offer_type,
                'title': title,
                'picture_1': temp_offer.get_absolute_picture_1_img,
                'picture_1_thumb': temp_offer.get_absolute_picture_1_thumbnail,
                'picture_2': temp_offer.get_absolute_picture_2_img,
                'picture_2_thumb': temp_offer.get_absolute_picture_2_thumbnail,
                'picture_3': temp_offer.get_absolute_picture_3_img,
                'picture_3_thumb': temp_offer.get_absolute_picture_3_thumbnail,
                'picture_4': temp_offer.get_absolute_picture_4_img,
                'picture_4_thumb': temp_offer.get_absolute_picture_4_thumbnail,
                'description': description,
                'price': price
            }
            # Categories
            offer_categories = str(request.data.get('offer_categories')).split(',')
            offer_categories = Categories.objects.filter(code_category__in=offer_categories)
            offer_categories_list = []
            for category in offer_categories:
                temp_offer.offer_categories.add(category.pk)
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
                temp_offer.for_whom.add(for_who.pk)
                offer_for_whom_list.append(
                    {
                        "pk": for_who.pk,
                        "code_for_whom": for_who.code_for_whom,
                        "name_for_whom": for_who.name_for_whom
                    }
                )
            data['for_whom'] = offer_for_whom_list
            # IF OFFER TYPE == V (VENTE) ; S (SERVICE)
            if offer_type == 'V':
                product_quantity = request.data.get('product_quantity')
                product_price_by = request.data.get('product_price_by')
                product_longitude = request.data.get('product_longitude')
                product_latitude = request.data.get('product_latitude')
                product_address = request.data.get('product_address')
                product_serializer = BaseTempShopProductSerializer(data={
                    'temp_offer': temp_offer_pk,
                    'product_quantity': product_quantity,
                    'product_price_by': product_price_by,
                    'product_longitude': product_longitude,
                    'product_latitude': product_latitude,
                    'product_address': product_address,
                })
                if product_serializer.is_valid():
                    product_valid = True
                    temp_product = product_serializer.save()
                    # Colors
                    colors = str(request.data.get('product_colors')).split(',')
                    colors = Colors.objects.filter(code_color__in=colors)
                    product_colors_list = []
                    for color in colors:
                        temp_product.product_colors.add(color.pk)
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
                        temp_product.product_sizes.add(size.pk)
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
                    'temp_offer': temp_offer_pk,
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
                    temp_service = service_serializer.save()
                    # Availability Days
                    availability_days = str(request.data.get('service_availability_days')).split(',')
                    availability_days = ServiceDays.objects.filter(code_day__in=availability_days)
                    service_availability_days_list = []
                    for availability_day in availability_days:
                        temp_service.service_availability_days.add(availability_day.pk)
                        service_availability_days_list.append(
                            {
                                "pk": availability_day.pk,
                                "code_day": availability_day.code_day,
                                "name_day": availability_day.name_day
                            }
                        )
                    data['service_availability_days'] = service_availability_days_list
                    # SERVICE RETURN DATA
                    data['service_morning_hour_from'] = temp_service.service_morning_hour_from
                    data['service_morning_hour_to'] = temp_service.service_morning_hour_to
                    data['service_afternoon_hour_from'] = temp_service.service_afternoon_hour_from
                    data['service_afternoon_hour_to'] = temp_service.service_afternoon_hour_to
                    data['service_zone_by'] = temp_service.service_zone_by
                    data['service_price_by'] = temp_service.service_price_by
                    data['service_longitude'] = temp_service.service_longitude
                    data['service_latitude'] = temp_service.service_latitude
                    data['service_address'] = temp_service.service_address
                    data['service_km_radius'] = temp_service.service_km_radius
                    # For services
                    return Response(data=data, status=status.HTTP_200_OK)
                else:
                    service_serializer_errors = service_serializer.errors

            # if product_valid:
            #     # Deliveries
            #     temp_delivery_city_1 = request.data.get('delivery_city_1', None)
            #     temp_delivery_price_1 = request.data.get('delivery_price_1', None)
            #     temp_delivery_days_1 = request.data.get('delivery_days_1', None)
            #     temp_delivery_city_2 = request.data.get('delivery_city_2', None)
            #     temp_delivery_price_2 = request.data.get('delivery_price_2', None)
            #     temp_delivery_days_2 = request.data.get('delivery_days_2', None)
            #     temp_delivery_city_3 = request.data.get('delivery_city_3', None)
            #     temp_delivery_price_3 = request.data.get('delivery_price_3', None)
            #     temp_delivery_days_3 = request.data.get('delivery_days_3', None)
            #
            #     delivery_serializer = BaseTempShopDeliverySerializer(data={
            #         'temp_offer': temp_offer_pk,
            #         'temp_delivery_city_1': temp_delivery_city_1,
            #         'temp_delivery_price_1': temp_delivery_price_1,
            #         'temp_delivery_days_1': temp_delivery_days_1,
            #         'temp_delivery_city_2': temp_delivery_city_2,
            #         'temp_delivery_price_2': temp_delivery_price_2,
            #         'temp_delivery_days_2': temp_delivery_days_2,
            #         'temp_delivery_city_3': temp_delivery_city_3,
            #         'temp_delivery_price_3': temp_delivery_price_3,
            #         'temp_delivery_days_3': temp_delivery_days_3,
            #     })
            #     if delivery_serializer.is_valid():
            #         delivery_serializer.save()
            #
            #         def removekey(d, key):
            #             r = dict(d)
            #             del r[key]
            #             return r
            #         temp_delivery = removekey(delivery_serializer.data, 'temp_offer')
            #         data['deliveries'] = temp_delivery
            #         # For products
            #         return Response(data=data, status=status.HTTP_200_OK)
            #     else:
            #         return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
                            'temp_offer': temp_offer_pk,
                            'temp_delivery_city': delivery_cities_1_pk,
                            'temp_delivery_price': float(delivery_price_1),
                            'temp_delivery_days': int(delivery_days_1)
                        }
                    )
                if delivery_city_2:
                    city_2_check = True
                    deliveries.append(
                        {
                            'temp_offer': temp_offer_pk,
                            'temp_delivery_city': delivery_cities_2_pk,
                            'temp_delivery_price': float(delivery_price_2),
                            'temp_delivery_days': int(delivery_days_2)
                        }
                    )
                if delivery_city_3:
                    city_3_check = True
                    deliveries.append(
                        {
                            'temp_offer': temp_offer_pk,
                            'temp_delivery_city': delivery_cities_3_pk,
                            'temp_delivery_price': float(delivery_price_3),
                            'temp_delivery_days': int(delivery_days_3)
                        }
                    )
                delivery_serializer = BaseTempShopDeliverySerializer(data=deliveries, many=True)
                if delivery_serializer.is_valid():
                    deliveries_serializer = delivery_serializer.save()
                    for delivery in deliveries_serializer:
                        if city_1_check:
                            delivery.temp_delivery_city.add(*delivery_cities_1_pk)
                            city_1_check = False
                        elif city_2_check:
                            delivery.temp_delivery_city.add(*delivery_cities_2_pk)
                            city_2_check = False
                        elif city_3_check:
                            delivery.temp_delivery_city.add(*delivery_cities_3_pk)
                            city_3_check = False
                    data['deliveries'] = deliveries
                    # For products
                    return Response(data=data, status=status.HTTP_200_OK)
                else:
                    return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                temp_offer.delete()
                if offer_type == 'V' and product_serializer_errors:
                    return Response(product_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
                if offer_type == 'S' and service_serializer_errors:
                    return Response(service_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(offer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        temp_offer_pk = request.data.get('temp_offer_pk')
        try:
            temp_offer = TempOffers.objects.get(pk=temp_offer_pk)
            temp_offer_pk = temp_offer.pk
            picture_1 = request.data.get('picture_1', None)
            picture_2 = request.data.get('picture_2', None)
            picture_3 = request.data.get('picture_3', None)
            picture_4 = request.data.get('picture_4', None)

            previous_images = list()
            previous_images.append(API_URL + temp_offer.picture_1.url
                                   if temp_offer.picture_1 else False)
            previous_images.append(API_URL + temp_offer.picture_2.url
                                   if temp_offer.picture_2 else False)
            previous_images.append(API_URL + temp_offer.picture_3.url
                                   if temp_offer.picture_3 else False)
            previous_images.append(API_URL + temp_offer.picture_4.url
                                   if temp_offer.picture_4 else False)

            if isinstance(picture_1, InMemoryUploadedFile):
                try:
                    picture_1_path = self.parent_file_dir + temp_offer.picture_1.url
                    picture_1_thumb_path = self.parent_file_dir + temp_offer.picture_1_thumbnail.url
                    remove(picture_1_path)
                    remove(picture_1_thumb_path)
                except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                    pass
                temp_offer.picture_1 = None
                temp_offer.save()
            else:
                # src
                if picture_1 in previous_images:
                    try:
                        img_1_index = previous_images.index(picture_1)
                        if img_1_index == 0:
                            picture_1 = temp_offer.picture_1
                        elif img_1_index == 1:
                            picture_1 = temp_offer.picture_2
                        elif img_1_index == 2:
                            picture_1 = temp_offer.picture_3
                        else:
                            picture_1 = temp_offer.picture_4
                    # None wasn't sent
                    except ValueError:
                        picture_1 = None

            if isinstance(picture_2, InMemoryUploadedFile):
                try:
                    picture_2_path = self.parent_file_dir + temp_offer.picture_2.url
                    picture_2_thumb_path = self.parent_file_dir + temp_offer.picture_2_thumbnail.url
                    remove(picture_2_path)
                    remove(picture_2_thumb_path)
                except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                    pass
                temp_offer.picture_2 = None
                temp_offer.save()
            else:
                # src
                if picture_2 in previous_images:
                    try:
                        img_2_index = previous_images.index(picture_2)
                        if img_2_index == 0:
                            picture_2 = temp_offer.picture_2
                        elif img_2_index == 1:
                            picture_2 = temp_offer.picture_2
                        elif img_2_index == 2:
                            picture_2 = temp_offer.picture_2
                        else:
                            picture_2 = temp_offer.picture_2
                    # None wasn't sent
                    except ValueError:
                        picture_2 = None

            if isinstance(picture_3, InMemoryUploadedFile):
                try:
                    picture_3_path = self.parent_file_dir + temp_offer.picture_3.url
                    picture_3_thumb_path = self.parent_file_dir + temp_offer.picture_3_thumbnail.url
                    remove(picture_3_path)
                    remove(picture_3_thumb_path)
                except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                    pass
                temp_offer.picture_3 = None
                temp_offer.save()
            else:
                # src
                if picture_3 in previous_images:
                    try:
                        img_3_index = previous_images.index(picture_3)
                        if img_3_index == 0:
                            picture_3 = temp_offer.picture_3
                        elif img_3_index == 1:
                            picture_3 = temp_offer.picture_3
                        elif img_3_index == 2:
                            picture_3 = temp_offer.picture_3
                        else:
                            picture_3 = temp_offer.picture_3
                    # None wasn't sent
                    except ValueError:
                        picture_3 = None

            if isinstance(picture_4, InMemoryUploadedFile):
                try:
                    picture_4_path = self.parent_file_dir + temp_offer.picture_4.url
                    picture_4_thumb_path = self.parent_file_dir + temp_offer.picture_4_thumbnail.url
                    remove(picture_4_path)
                    remove(picture_4_thumb_path)
                except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                    pass
                temp_offer.picture_4 = None
                temp_offer.save()
            else:
                # src
                if picture_4 in previous_images:
                    try:
                        img_4_index = previous_images.index(picture_4)
                        if img_4_index == 0:
                            picture_4 = temp_offer.picture_4
                        elif img_4_index == 1:
                            picture_4 = temp_offer.picture_4
                        elif img_4_index == 2:
                            picture_4 = temp_offer.picture_4
                        else:
                            picture_4 = temp_offer.picture_4
                    # None wasn't sent
                    except ValueError:
                        picture_4 = None

            title = request.data.get('title', '')
            description = request.data.get('description', '')
            price = request.data.get('price', '')
            # Temp product PUT serializer
            temp_offer_serializer = BaseTempOfferPutSerializer(data={
                'title': title,
                'picture_1': picture_1,
                'picture_2': picture_2,
                'picture_3': picture_3,
                'picture_4': picture_4,
                'description': description,
                'price': price,
            })
            if temp_offer_serializer.is_valid():
                offer_type = temp_offer.offer_type
                product_valid = False
                service_valid = False
                product_serializer_errors = None
                service_serializer_errors = None
                temp_product_serializer = None
                temp_service_serializer = None
                # Generate thumbnails
                base_generate_offer_thumbnails.apply_async((temp_offer_pk, 'TempOffers'), )
                if temp_offer.offer_type == 'V':
                    product_quantity = request.data.get('product_quantity', '')
                    product_price_by = request.data.get('product_price_by', '')
                    product_longitude = request.data.get('product_longitude', '')
                    product_latitude = request.data.get('product_latitude', '')
                    product_address = request.data.get('product_address', '')
                    temp_product_serializer = BaseTempProductPutSerializer(data={
                        'product_quantity': product_quantity,
                        'product_price_by': product_price_by,
                        'product_longitude': product_longitude,
                        'product_latitude': product_latitude,
                        'product_address': product_address,
                    })
                    if temp_product_serializer.is_valid():
                        product_valid = True
                    else:
                        product_serializer_errors = temp_product_serializer.errors
                elif temp_offer.offer_type == 'S':
                    service_morning_hour_from = request.data.get('service_morning_hour_from', '')
                    service_morning_hour_to = request.data.get('service_morning_hour_to', '')
                    service_afternoon_hour_from = request.data.get('service_afternoon_hour_from', '')
                    service_afternoon_hour_to = request.data.get('service_afternoon_hour_to', '')
                    service_zone_by = request.data.get('service_zone_by', '')
                    service_price_by = request.data.get('service_price_by', '')
                    service_longitude = request.data.get('service_longitude', '')
                    service_latitude = request.data.get('service_latitude', '')
                    service_address = request.data.get('service_address', '')
                    temp_service_serializer = BaseTempServicePutSerializer(data={
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
                    if temp_service_serializer.is_valid():
                        service_valid = True
                    else:
                        service_serializer_errors = temp_service_serializer.errors
                if product_valid or service_valid:
                    # UPDATE OFFER TABLE
                    temp_updated_offer = temp_offer_serializer.update(temp_offer,
                                                                      temp_offer_serializer.validated_data)
                    data = {
                        'pk': temp_updated_offer.pk,
                        'offer_type': temp_updated_offer.offer_type,
                        'title': temp_updated_offer.title,
                        'picture_1': temp_updated_offer.get_absolute_picture_1_img,
                        'picture_1_thumb': temp_updated_offer.get_absolute_picture_1_thumbnail,
                        'picture_2': temp_updated_offer.get_absolute_picture_2_img,
                        'picture_2_thumb': temp_updated_offer.get_absolute_picture_2_thumbnail,
                        'picture_3': temp_updated_offer.get_absolute_picture_3_img,
                        'picture_3_thumb': temp_updated_offer.get_absolute_picture_3_thumbnail,
                        'picture_4': temp_updated_offer.get_absolute_picture_4_img,
                        'picture_4_thumb': temp_updated_offer.get_absolute_picture_4_thumbnail,
                        'description': temp_updated_offer.description,
                        'price': temp_updated_offer.price
                    }
                    # UPDATE CATEGORIES
                    temp_offer.offer_categories.clear()
                    offer_categories = str(request.data.get('offer_categories')).split(',')
                    new_categories = Categories.objects.filter(code_category__in=offer_categories)
                    offer_categories_list = []
                    for category in new_categories:
                        temp_offer.offer_categories.add(category.pk)
                        offer_categories_list.append(
                            {
                                "pk": category.pk,
                                "code_category": category.code_category,
                                "name_category": category.name_category
                            }
                        )
                    data['offer_categories'] = offer_categories_list
                    # UPDATE FOR WHOM
                    temp_offer.for_whom.clear()
                    offer_for_whom = str(request.data.get('for_whom')).split(',')
                    new_for_whom = ForWhom.objects.filter(code_for_whom__in=offer_for_whom)
                    offer_for_whom_list = []
                    for for_who in new_for_whom:
                        temp_offer.for_whom.add(for_who.pk)
                        offer_for_whom_list.append(
                            {
                                "pk": for_who.pk,
                                "code_for_whom": for_who.code_for_whom,
                                "name_for_whom": for_who.name_for_whom
                            }
                        )
                    data['for_whom'] = offer_for_whom_list
                    if product_valid:
                        temp_product = TempProducts.objects.get(temp_offer=temp_offer.pk)
                        # serializer referenced before assignment fixed by the product_valid = True
                        temp_updated_product = temp_product_serializer.update(temp_product,
                                                                              temp_product_serializer.validated_data)
                        # UPDATE COLORS
                        temp_product.product_colors.clear()
                        colors = str(request.data.get('product_colors')).split(',')
                        new_colors = Colors.objects.filter(code_color__in=colors)
                        product_colors_list = []
                        for color in new_colors:
                            temp_product.product_colors.add(color.pk)
                            product_colors_list.append(
                                {
                                    "pk": color.pk,
                                    "code_color": color.code_color,
                                    "name_color": color.name_color
                                }
                            )
                        data['product_colors'] = product_colors_list
                        # UPDATE SIZES
                        temp_product.product_sizes.clear()
                        sizes = str(request.data.get('product_sizes')).split(',')
                        new_sizes = Sizes.objects.filter(code_size__in=sizes)
                        product_sizes_list = []
                        for size in new_sizes:
                            temp_product.product_sizes.add(size.pk)
                            product_sizes_list.append(
                                {
                                    "pk": size.pk,
                                    "code_size": size.code_size,
                                    "name_size": size.name_size
                                }
                            )
                        data['product_sizes'] = product_sizes_list
                        # PRODUCT RETURN DATA
                        data['product_quantity'] = temp_updated_product.product_quantity
                        data['product_price_by'] = temp_updated_product.product_price_by
                        data['product_longitude'] = temp_updated_product.product_longitude
                        data['product_latitude'] = temp_updated_product.product_latitude
                        data['product_address'] = temp_updated_product.product_address
                        # # UPDATE DELIVERIES
                        # temp_delivery_city_1 = request.data.get('delivery_city_1')
                        # temp_delivery_price_1 = request.data.get('delivery_price_1', None)
                        # temp_delivery_days_1 = request.data.get('delivery_days_1', None)
                        #
                        # temp_delivery_city_2 = request.data.get('delivery_city_2', None)
                        # temp_delivery_price_2 = request.data.get('delivery_price_2', None)
                        # temp_delivery_days_2 = request.data.get('delivery_days_2', None)
                        #
                        # temp_delivery_city_3 = request.data.get('delivery_city_3', None)
                        # temp_delivery_price_3 = request.data.get('delivery_price_3', None)
                        # temp_delivery_days_3 = request.data.get('delivery_days_3', None)
                        #
                        # delivery_serializer = BaseTempShopDeliveryPUTSerializer(data={
                        #     'temp_delivery_city_1': temp_delivery_city_1,
                        #     'temp_delivery_price_1': temp_delivery_price_1,
                        #     'temp_delivery_days_1': temp_delivery_days_1,
                        #     'temp_delivery_city_2': temp_delivery_city_2,
                        #     'temp_delivery_price_2': temp_delivery_price_2,
                        #     'temp_delivery_days_2': temp_delivery_days_2,
                        #     'temp_delivery_city_3': temp_delivery_city_3,
                        #     'temp_delivery_price_3': temp_delivery_price_3,
                        #     'temp_delivery_days_3': temp_delivery_days_3,
                        # })
                        # if delivery_serializer.is_valid():
                        #     temp_delivery = TempDelivery.objects.get(temp_offer=temp_offer_pk)
                        #     delivery_serializer.update(temp_delivery, delivery_serializer.validated_data)
                        #     data['deliveries'] = delivery_serializer.data
                        #     return Response(data, status=status.HTTP_200_OK)
                        # else:
                        #     return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                        # UPDATE DELIVERIES
                        temp_offer.temp_offer_delivery.all().delete()
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
                                    'temp_offer': temp_offer_pk,
                                    'temp_delivery_city': delivery_cities_1_pk,
                                    'temp_delivery_price': float(delivery_price_1),
                                    'temp_delivery_days': int(delivery_days_1)
                                }
                            )
                        if delivery_city_2:
                            city_2_check = True
                            deliveries.append(
                                {
                                    'temp_offer': temp_offer_pk,
                                    'temp_delivery_city': delivery_cities_2_pk,
                                    'temp_delivery_price': float(delivery_price_2),
                                    'temp_delivery_days': int(delivery_days_2)
                                }
                            )
                        if delivery_city_3:
                            city_3_check = True
                            deliveries.append(
                                {
                                    'temp_offer': temp_offer_pk,
                                    'temp_delivery_city': delivery_cities_3_pk,
                                    'temp_delivery_price': float(delivery_price_3),
                                    'temp_delivery_days': int(delivery_days_3)
                                }
                            )

                        # Save edited deliveries
                        delivery_serializer = BaseTempShopDeliverySerializer(data=deliveries, many=True)
                        if delivery_serializer.is_valid():
                            # Delete old deliveries cities
                            TempDelivery.objects.filter(temp_offer__pk=temp_offer_pk).delete()
                            # Add new deliveries
                            deliveries_serializer = delivery_serializer.save()
                            for delivery in deliveries_serializer:
                                if city_1_check:
                                    delivery.temp_delivery_city.add(*delivery_cities_1_pk)
                                    city_1_check = False
                                elif city_2_check:
                                    delivery.temp_delivery_city.add(*delivery_cities_2_pk)
                                    city_2_check = False
                                elif city_3_check:
                                    delivery.temp_delivery_city.add(*delivery_cities_3_pk)
                                    city_3_check = False
                            data['deliveries'] = deliveries
                            return Response(data, status=status.HTTP_200_OK)
                        else:
                            return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    if service_valid:
                        temp_service = TempServices.objects.get(temp_offer=temp_offer.pk)
                        # serializer referenced before assignment fixed by the service_valid = True
                        temp_updated_service = temp_service_serializer.update(temp_service,
                                                                              temp_service_serializer.validated_data)
                        # UPDATE AVAILABILITY DAYS
                        temp_service.service_availability_days.clear()
                        availability_days = str(request.data.get('service_availability_days')).split(',')
                        new_availability_days = ServiceDays.objects.filter(code_day__in=availability_days)
                        service_availability_days_list = []
                        for availability_day in new_availability_days:
                            temp_service.service_availability_days.add(availability_day.pk)
                            service_availability_days_list.append(
                                {
                                    "pk": availability_day.pk,
                                    "code_day": availability_day.code_size,
                                    "name_day": availability_day.name_size
                                }
                            )
                        data['service_availability_days'] = service_availability_days_list
                        # SERVICE RETURN DATA
                        data['service_morning_hour_from'] = temp_updated_service.service_morning_hour_from
                        data['service_morning_hour_to'] = temp_updated_service.service_morning_hour_to
                        data['service_afternoon_hour_from'] = temp_updated_service.service_afternoon_hour_from
                        data['service_afternoon_hour_to'] = temp_updated_service.service_afternoon_hour_to
                        data['service_zone_by'] = temp_updated_service.service_zone_by
                        data['service_price_by'] = temp_updated_service.service_price_by
                        data['service_longitude'] = temp_updated_service.service_longitude
                        data['service_latitude'] = temp_updated_service.service_latitude
                        data['service_address'] = temp_updated_service.service_address
                        data['service_km_radius'] = temp_updated_service.service_km_radius
                        return Response(data, status=status.HTTP_200_OK)
                else:
                    if offer_type == 'V' and product_serializer_errors:
                        return Response(product_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
                    if offer_type == 'S' and service_serializer_errors:
                        return Response(service_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(temp_offer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except TempOffers.DoesNotExist:
            data = {'errors': ['Temp offer not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        temp_offer_pk = request.data.get('temp_offer_id')
        unique_id = request.data.get('unique_id')
        try:
            temp_offer = TempOffers.objects.get(pk=temp_offer_pk)
            if temp_offer.temp_shop.unique_id != unique_id:
                data = {'errors': ['Temp offer not yours to delete.']}
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
            # Delete temp product images
            # Picture 1
            try:
                picture_1 = temp_offer.picture_1.path
                remove(picture_1)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 1 thumbnail
            try:
                picture_1_thumbnail = temp_offer.picture_1_thumbnail.path
                remove(picture_1_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 2
            try:
                picture_2 = temp_offer.picture_2.path
                remove(picture_2)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 2 thumbnail
            try:
                picture_2_thumbnail = temp_offer.picture_2_thumbnail.path
                remove(picture_2_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 3
            try:
                picture_3 = temp_offer.picture_3.path
                remove(picture_3)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 3 thumbnail
            try:
                picture_3_thumbnail = temp_offer.picture_3_thumbnail.path
                remove(picture_3_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 4
            try:
                picture_4 = temp_offer.picture_4.path
                remove(picture_4)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            # Picture 4 thumbnail
            try:
                picture_4_thumbnail = temp_offer.picture_4_thumbnail.path
                remove(picture_4_thumbnail)
            except (FileNotFoundError, ValueError, AttributeError):
                pass
            temp_offer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TempOffers.DoesNotExist:
            data = {'errors': ['Temp offer not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetOneTempOfferView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        temp_offer_id = kwargs.get('temp_offer_id')
        try:
            temp_offer = TempOffers.objects \
                .select_related('temp_offer_solder') \
                .select_related('temp_offer_products') \
                .select_related('temp_offer_services') \
                .prefetch_related('temp_offer_delivery') \
                .get(pk=temp_offer_id)
            temp_offer_details_serializer = BaseTempOfferDetailsSerializer(temp_offer)
            return Response(temp_offer_details_serializer.data, status=status.HTTP_200_OK)
        except TempOffers.DoesNotExist:
            data = {'errors': ['Temp offer not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetTempShopOffersListView(APIView, PaginationMixinBy5):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        try:
            temp_shop = TempShop.objects.get(unique_id=unique_id)
            temp_offers = TempOffers.objects \
                .select_related('temp_offer_solder') \
                .select_related('temp_offer_products') \
                .select_related('temp_offer_services') \
                .prefetch_related('temp_offer_delivery') \
                .filter(temp_shop=temp_shop).order_by('-created_date')
            page = self.paginate_queryset(queryset=temp_offers)
            if page is not None:
                serializer = BaseTempOfferssListSerializer(instance=page, many=True)
                return self.get_paginated_response(serializer.data)
            data = {'response': 'Temp shop has no products.'}
            return Response(data=data, status=status.HTTP_200_OK)
        except TempShop.DoesNotExist:
            data = {'errors': ['Temp shop unique_id not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class TempShopOfferSolderView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        temp_offer_id = kwargs.get('temp_offer_id')
        try:
            temp_solder = TempSolder.objects.get(temp_offer=temp_offer_id)
            temp_offer_details_serializer = BaseTempShopOfferSolderSerializer(temp_solder)
            return Response(temp_offer_details_serializer.data, status=status.HTTP_200_OK)
        except TempSolder.DoesNotExist:
            data = {'errors': ['Temp offer solder not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def post(request, *args, **kwargs):
        temp_offer_id = request.data.get('temp_offer_id')
        temp_offer = TempOffers.objects.get(pk=temp_offer_id).pk
        serializer = BaseTempShopOfferSolderSerializer(data={
            'temp_offer': temp_offer,
            'temp_solder_type': request.data.get('temp_solder_type'),
            'temp_solder_value': request.data.get('temp_solder_value'),
        })
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(request, *args, **kwargs):
        temp_offer_id = request.data.get('temp_offer_id')
        temp_solder = TempSolder.objects.get(temp_offer=temp_offer_id)
        serializer = BaseTempShopOfferSolderPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(temp_solder, serializer.validated_data)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        data = {}
        temp_offer_id = request.data.get('temp_offer_id')
        try:
            TempSolder.objects.get(temp_offer=temp_offer_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TempSolder.DoesNotExist:
            data['errors'] = ["Temp offer solder not found."]
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class TempShopOfferDuplicateView(APIView):
    permission_classes = (permissions.AllowAny,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    @staticmethod
    def post(request, *args, **kwargs):
        temp_offer_id = request.data.get('temp_offer_id')
        temp_offer = TempOffers.objects \
            .select_related('temp_offer_solder') \
            .select_related('temp_offer_products') \
            .select_related('temp_offer_services') \
            .prefetch_related('temp_offer_delivery') \
            .get(pk=temp_offer_id)
        # Title
        title = temp_offer.title
        # Description
        description = temp_offer.description
        # Price
        price = temp_offer.price
        # Offer type
        offer_type = temp_offer.offer_type
        temp_offer_serializer = BaseTempShopOfferDuplicateSerializer(data={
            'temp_shop': temp_offer.temp_shop.pk,
            'offer_type': offer_type,
            'title': title,
            'picture_1': temp_offer.picture_1 if temp_offer.picture_1 else None,
            'picture_2': temp_offer.picture_2 if temp_offer.picture_2 else None,
            'picture_3': temp_offer.picture_3 if temp_offer.picture_3 else None,
            'picture_4': temp_offer.picture_4 if temp_offer.picture_4 else None,
            'picture_1_thumbnail': temp_offer.picture_1_thumbnail if temp_offer.picture_1_thumbnail else None,
            'picture_2_thumbnail': temp_offer.picture_2_thumbnail if temp_offer.picture_2_thumbnail else None,
            'picture_3_thumbnail': temp_offer.picture_3_thumbnail if temp_offer.picture_3_thumbnail else None,
            'picture_4_thumbnail': temp_offer.picture_4_thumbnail if temp_offer.picture_4_thumbnail else None,
            'description': description,
            'price': price
        })
        if temp_offer_serializer.is_valid():
            # Duplicate offer
            temp_offer_serializer = temp_offer_serializer.save()
            # Duplicate pictures
            base_duplicate_offer_images.apply_async(args=(temp_offer.pk, temp_offer_serializer.pk, 'TempOffers'), )
            # Solder
            try:
                product_solder = temp_offer.temp_offer_solder
                solder_serializer = BaseTempShopOfferSolderSerializer(data={
                    'temp_offer': temp_offer_serializer.pk,
                    'temp_solder_type': product_solder.temp_solder_type,
                    'temp_solder_value': product_solder.temp_solder_value
                })
                if solder_serializer.is_valid():
                    solder_serializer.save()
            except ObjectDoesNotExist:
                pass
            data = {
                'pk': temp_offer_serializer.pk,
                'offer_type': temp_offer_serializer.offer_type,
                'title': temp_offer_serializer.title,
                'picture_1': temp_offer_serializer.get_absolute_picture_1_img,
                'picture_1_thumb': temp_offer_serializer.get_absolute_picture_1_thumbnail,
                'picture_2': temp_offer_serializer.get_absolute_picture_2_img,
                'picture_2_thumb': temp_offer_serializer.get_absolute_picture_2_thumbnail,
                'picture_3': temp_offer_serializer.get_absolute_picture_3_img,
                'picture_3_thumb': temp_offer_serializer.get_absolute_picture_3_thumbnail,
                'picture_4': temp_offer_serializer.get_absolute_picture_4_img,
                'picture_4_thumb': temp_offer_serializer.get_absolute_picture_4_thumbnail,
                'description': temp_offer_serializer.description,
                'price': temp_offer_serializer.price
            }
            # Categories
            offer_categories = list(temp_offer.offer_categories.all().values_list('pk', flat=True))
            offer_categories = Categories.objects.filter(pk__in=offer_categories)
            offer_categories_list = []
            for category in offer_categories:
                temp_offer_serializer.offer_categories.add(category.pk)
                offer_categories_list.append(
                    {
                        "pk": category.pk,
                        "code_category": category.code_category,
                        "name_category": category.name_category
                    }
                )
            data['offer_categories'] = offer_categories_list
            # For whom
            for_whom = list(temp_offer.for_whom.all().values_list('pk', flat=True))
            for_whom = ForWhom.objects.filter(pk__in=for_whom)
            offer_for_whom_list = []
            for for_who in for_whom:
                temp_offer_serializer.for_whom.add(for_who.pk)
                offer_for_whom_list.append(
                    {
                        "pk": for_who.pk,
                        "code_for_whom": for_who.code_for_whom,
                        "name_for_whom": for_who.name_for_whom
                    }
                )
            data['for_whom'] = offer_for_whom_list
            # Duplicate Product
            product_valid = False
            product_serializer_errors = None
            service_serializer_errors = None
            if temp_offer_serializer.offer_type == 'V':
                product_quantity = temp_offer.temp_offer_products.product_quantity
                product_price_by = temp_offer.temp_offer_products.product_price_by
                product_longitude = temp_offer.temp_offer_products.product_longitude
                product_latitude = temp_offer.temp_offer_products.product_latitude
                product_address = temp_offer.temp_offer_products.product_address
                temp_product_serializer = BaseTempShopProductSerializer(data={
                    'temp_offer': temp_offer_serializer.pk,
                    'product_quantity': product_quantity,
                    'product_price_by': product_price_by,
                    'product_longitude': product_longitude,
                    'product_latitude': product_latitude,
                    'product_address': product_address,
                })
                if temp_product_serializer.is_valid():
                    product_valid = True
                    temp_product_serializer.save()
                    # Color
                    colors = list(temp_offer.temp_offer_products.product_colors.all().values_list('pk', flat=True))
                    colors = Colors.objects.filter(pk__in=colors)
                    product_colors_list = []
                    for color in colors:
                        temp_offer_serializer.temp_offer_products.product_colors.add(color.pk)
                        product_colors_list.append(
                            {
                                "pk": color.pk,
                                "code_color": color.code_color,
                                "name_color": color.name_color
                            }
                        )
                    data['product_colors'] = product_colors_list
                    # Size
                    sizes = list(temp_offer.temp_offer_products.product_sizes.all().values_list('pk', flat=True))
                    sizes = Sizes.objects.filter(pk__in=sizes)
                    product_sizes_list = []
                    for size in sizes:
                        temp_offer_serializer.temp_offer_products.product_sizes.add(size.pk)
                        product_sizes_list.append(
                            {
                                "pk": size.pk,
                                "code_color": size.code_size,
                                "name_color": size.name_size
                            }
                        )
                    data['product_sizes'] = product_sizes_list
                else:
                    product_serializer_errors = temp_product_serializer.errors
            # Duplicate Service
            elif temp_offer_serializer.offer_type == 'S':
                service_morning_hour_from = temp_offer.temp_offer_services.service_morning_hour_from
                service_morning_hour_to = temp_offer.temp_offer_services.service_morning_hour_to
                service_afternoon_hour_from = temp_offer.temp_offer_services.service_afternoon_hour_from
                service_afternoon_hour_to = temp_offer.temp_offer_services.service_afternoon_hour_to
                service_zone_by = temp_offer.temp_offer_services.service_zone_by
                service_price_by = temp_offer.temp_offer_services.service_price_by
                service_longitude = temp_offer.temp_offer_services.service_longitude
                service_latitude = temp_offer.temp_offer_services.service_latitude
                service_address = temp_offer.temp_offer_services.service_address
                temp_service_serializer = BaseTempShopServiceSerializer(data={
                    'temp_offer': temp_offer_serializer.pk,
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
                if temp_service_serializer.is_valid():
                    temp_service_serializer = temp_service_serializer.save()
                    # Availability Days
                    availability_days = list(temp_offer.temp_offer_services.service_availability_days.all()
                                             .values_list('pk', flat=True))
                    availability_days = ServiceDays.objects.filter(pk__in=availability_days)
                    service_availability_days_list = []
                    for availability_day in availability_days:
                        temp_service_serializer.service_availability_days.add(availability_day.pk)
                        service_availability_days_list.append(
                            {
                                "pk": availability_day.pk,
                                "code_day": availability_day.code_day,
                                "name_day": availability_day.name_day
                            }
                        )
                    data['service_availability_days'] = service_availability_days_list
                else:
                    service_serializer_errors = temp_service_serializer.errors
            if product_valid:
                deliveries = temp_offer.temp_offer_delivery.all()
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
                    delivery_price_1 = deliveries[0].temp_delivery_price
                    delivery_days_1 = deliveries[0].temp_delivery_days
                    delivery_city_1 = deliveries[0].temp_delivery_city.all().values_list('pk', flat=True)
                    delivery_price_2 = deliveries[1].temp_delivery_price
                    delivery_days_2 = deliveries[1].temp_delivery_days
                    delivery_city_2 = deliveries[1].temp_delivery_city.all().values_list('pk', flat=True)
                    delivery_price_3 = deliveries[2].temp_delivery_price
                    delivery_days_3 = deliveries[2].temp_delivery_days
                    delivery_city_3 = deliveries[2].temp_delivery_city.all().values_list('pk', flat=True)
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
                            'temp_offer': temp_offer_serializer.pk,
                            'temp_delivery_city': delivery_cities_1_pk,
                            'temp_delivery_price': float(delivery_price_1),
                            'temp_delivery_days': int(delivery_days_1)
                        }
                    )
                if delivery_city_2:
                    city_2_check = True
                    deliveries.append(
                        {
                            'temp_offer': temp_offer_serializer.pk,
                            'temp_delivery_city': delivery_cities_2_pk,
                            'temp_delivery_price': float(delivery_price_2),
                            'temp_delivery_days': int(delivery_days_2)
                        }
                    )
                if delivery_city_3:
                    city_3_check = True
                    deliveries.append(
                        {
                            'temp_offer': temp_offer_serializer.pk,
                            'temp_delivery_city': delivery_cities_3_pk,
                            'temp_delivery_price': float(delivery_price_3),
                            'temp_delivery_days': int(delivery_days_3)
                        }
                    )
                delivery_serializer = BaseTempShopDeliverySerializer(data=deliveries, many=True)
                if delivery_serializer.is_valid():
                    deliveries_serializer = delivery_serializer.save()
                    for delivery in deliveries_serializer:
                        if city_1_check:
                            delivery.temp_delivery_city.add(*delivery_cities_1_pk)
                            city_1_check = False
                        elif city_2_check:
                            delivery.temp_delivery_city.add(*delivery_cities_2_pk)
                            city_2_check = False
                        elif city_3_check:
                            delivery.temp_delivery_city.add(*delivery_cities_3_pk)
                            city_3_check = False
                    data['deliveries'] = deliveries
                    return Response(data=data, status=status.HTTP_200_OK)
                else:
                    return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                temp_offer_serializer.delete()
                if offer_type == 'V' and product_serializer_errors:
                    return Response(product_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
                if offer_type == 'S' and service_serializer_errors:
                    return Response(service_serializer_errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(temp_offer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetLastThreeTempDeliveriesView(APIView):
    permission_classes = (permissions.AllowAny,)

    # @staticmethod
    # def get(request, *args, **kwargs):
    #     unique_id = kwargs.get('unique_id')
    #     try:
    #         temp_shop = TempShop.objects.get(unique_id=unique_id)
    #         temp_offers = TempOffers.objects \
    #             .select_related('temp_offer_products') \
    #             .prefetch_related('temp_offer_delivery') \
    #             .filter(temp_shop=temp_shop).order_by('-created_date')
    #         data = {
    #             'temp_delivery_city_1': None,
    #             'temp_delivery_price_1': None,
    #             'temp_delivery_days_1': None,
    #             'temp_delivery_city_2': None,
    #             'temp_delivery_price_2': None,
    #             'temp_delivery_days_2': None,
    #             'temp_delivery_city_3': None,
    #             'temp_delivery_price_3': None,
    #             'temp_delivery_days_3': None
    #         }
    #         delivery_1 = False
    #         delivery_2 = False
    #         delivery_3 = False
    #         for temp_offer in temp_offers:
    #             if not delivery_1:
    #                 if temp_offer.temp_offer_delivery.temp_delivery_city_1:
    #                     data['temp_delivery_city_1'] = temp_offer.temp_offer_delivery.temp_delivery_city_1
    #                     data['temp_delivery_price_1'] = temp_offer.temp_offer_delivery.temp_delivery_price_1
    #                     data['temp_delivery_days_1'] = temp_offer.temp_offer_delivery.temp_delivery_days_1
    #                     delivery_1 = True
    #             if not delivery_2:
    #                 if temp_offer.temp_offer_delivery.temp_delivery_city_2:
    #                     data['temp_delivery_city_2'] = temp_offer.temp_offer_delivery.temp_delivery_city_2
    #                     data['temp_delivery_price_2'] = temp_offer.temp_offer_delivery.temp_delivery_price_2
    #                     data['temp_delivery_days_2'] = temp_offer.temp_offer_delivery.temp_delivery_days_2
    #                     delivery_2 = True
    #             if not delivery_3:
    #                 if temp_offer.temp_offer_delivery.temp_delivery_city_3:
    #                     data['temp_delivery_city_3'] = temp_offer.temp_offer_delivery.temp_delivery_city_3
    #                     data['temp_delivery_price_3'] = temp_offer.temp_offer_delivery.temp_delivery_price_3
    #                     data['temp_delivery_days_3'] = temp_offer.temp_offer_delivery.temp_delivery_days_3
    #                     delivery_3 = True
    #         return Response(data=data, status=status.HTTP_200_OK)
    #     except TempOffers.DoesNotExist:
    #         data = {'errors': ['Temp shop unique_id not found.']}
    #         return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get(request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        try:
            temp_shop = TempShop.objects.get(unique_id=unique_id)
            temp_offers = TempOffers.objects \
                .select_related('temp_offer_products') \
                .prefetch_related('temp_offer_delivery') \
                .filter(temp_shop=temp_shop).order_by('-created_date')
            data = defaultdict(list)
            for temp_offer in temp_offers:
                temp_deliveries = temp_offer.temp_offer_delivery.all().order_by('-pk')
                for temp_delivery in temp_deliveries:
                    deliveries_list = {
                        'pk': '',
                        'temp_delivery_city': '',
                        'temp_delivery_price': '',
                        'temp_delivery_days': '',
                    }
                    dict_title = "deliveries"
                    deliveries_list['pk'] = temp_delivery.pk
                    deliveries_list['temp_delivery_city'] = temp_delivery.temp_delivery_city.all() \
                        .values_list('name_en', flat=True)
                    deliveries_list['temp_delivery_price'] = temp_delivery.temp_delivery_price
                    deliveries_list['temp_delivery_days'] = temp_delivery.temp_delivery_days
                    data[dict_title].append(deliveries_list)
                    if len(data['deliveries']) == 3:
                        break
                if len(data['deliveries']) == 3:
                    break
            return Response(data, status=status.HTTP_200_OK)
        except TempOffers.DoesNotExist:
            data = {'errors': ['Temp shop unique_id not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetLastTempUsedLocalisationView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        offer_type = kwargs.get('temp_offer_type')
        try:
            temp_shop = TempShop.objects.get(unique_id=unique_id)
            temp_offer = TempOffers.objects \
                .select_related('temp_offer_products') \
                .select_related('temp_offer_services') \
                .prefetch_related('temp_offer_delivery') \
                .filter(temp_shop=temp_shop).order_by('-created_date').last()
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
            if temp_offer.offer_type == offer_type:
                if temp_offer.temp_offer_products.product_address:
                    data_product['longitude'] = temp_offer.temp_offer_products.product_longitude
                    data_product['latitude'] = temp_offer.temp_offer_products.product_latitude
                    data_product['localisation_name'] = temp_offer.temp_offer_products.product_address
                    return Response(data=data_product, status=status.HTTP_200_OK)
            elif temp_offer.offer_type == offer_type:
                if temp_offer.temp_offer_services.service_address:
                    data_service['zone_by'] = temp_offer.temp_offer_services.service_zone_by
                    data_service['longitude'] = temp_offer.temp_offer_services.service_longitude
                    data_service['latitude'] = temp_offer.temp_offer_services.service_latitude
                    data_service['km_radius'] = temp_offer.temp_offer_services.service_km_radius
                    data_service['localisation_name'] = temp_offer.temp_offer_services.service_address
                    return Response(data=data_service, status=status.HTTP_200_OK)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TempOffers.DoesNotExist:
            data = {'errors': ['Temp shop unique_id not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
