from django.core.exceptions import SuspiciousFileOperation
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from temp_product.base.serializers import BaseTempShopProductSerializer, \
    BaseTempShopDeliverySerializer, BaseTempProductDetailsSerializer, \
    BaseTempProductsListSerializer, TempProductPutSerializer, \
    BaseTempShopSolderSerializer, BaseTempShopSolderPutSerializer
from os import rename, path, remove
from Qaryb_API_new.settings import IMAGES_ROOT_NAME, PRODUCT_IMAGES_BASE_NAME, API_URL
from uuid import uuid4
from temp_product.base.tasks import base_generate_product_thumbnails
from temp_product.base.models import TempShop, TempProduct, TempDelivery, TempSolder
from auth_shop.models import Categories, Colors, Sizes, ForWhom
from places.base.models import Cities
from temp_product.mixins import PaginationMixinBy5


class TempShopProductView(APIView):
    permission_classes = (permissions.AllowAny,)
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))

    def rename_product_pictures(self, picture):
        picture_name, picture_extension = path.splitext(str(picture))
        picture_id_name = str(uuid4()) + str(picture_extension)
        try:
            rename(self.parent_file_dir + IMAGES_ROOT_NAME + 'media/' +
                   picture_name + picture_extension,
                   self.parent_file_dir + PRODUCT_IMAGES_BASE_NAME + '/' + picture_id_name)
        except FileNotFoundError:
            pass
        return PRODUCT_IMAGES_BASE_NAME + '/' + picture_id_name

    def post(self, request, *args, **kwargs):
        unique_id = request.data.get('unique_id')
        temp_shop = TempShop.objects.get(unique_id=unique_id).pk
        serializer = BaseTempShopProductSerializer(data={
            'temp_shop': temp_shop,
            'product_type': request.data.get('product_type'),
            'product_name': request.data.get('product_name'),
            'picture_1': request.data.get('picture_1', None),
            'picture_2': request.data.get('picture_2', None),
            'picture_3': request.data.get('picture_3', None),
            'picture_4': request.data.get('picture_4', None),
            'description': request.data.get('description'),
            'quantity': request.data.get('quantity'),
            'price': request.data.get('price'),
            'price_by': request.data.get('price_by'),
            'shop_longitude': request.data.get('shop_longitude'),
            'shop_latitude': request.data.get('shop_latitude'),
            'shop_address': request.data.get('shop_address'),
        })
        if serializer.is_valid():
            temp_product = serializer.save()
            if temp_product.picture_1:
                temp_product.picture_1 = self.rename_product_pictures(temp_product.picture_1)
                temp_product.save()
            if temp_product.picture_2:
                temp_product.picture_2 = self.rename_product_pictures(temp_product.picture_2)
                temp_product.save()
            if temp_product.picture_3:
                temp_product.picture_3 = self.rename_product_pictures(temp_product.picture_3)
                temp_product.save()
            if temp_product.picture_4:
                temp_product.picture_4 = self.rename_product_pictures(temp_product.picture_4)
                temp_product.save()
            temp_product_pk = temp_product.pk

            # Generate thumbnails
            base_generate_product_thumbnails.apply_async((temp_product_pk,), )

            data = {
                "pk": temp_product.pk,
                "picture_1": temp_product.get_absolute_picture_1_img,
                "picture_1_thumb": temp_product.get_absolute_picture_1_thumbnail,
                "picture_2": temp_product.get_absolute_picture_2_img,
                "picture_2_thumb": temp_product.get_absolute_picture_2_thumbnail,
                "picture_3": temp_product.get_absolute_picture_3_img,
                "picture_3_thumb": temp_product.get_absolute_picture_3_thumbnail,
                "picture_4": temp_product.get_absolute_picture_4_img,
                "picture_4_thumb": temp_product.get_absolute_picture_4_thumbnail,
                "product_name": temp_product.product_name,
                "store_name": temp_product.temp_shop.shop_name,
                "product_categories": [
                ],
                "description": temp_product.description,
                "product_colors": [
                ],
                "product_size": [
                ],
                "for_whom": [
                ],
                "price": temp_product.price,
                "price_by": temp_product.price_by,
                "click_and_collect": [
                    {
                        "shop_longitude": temp_product.shop_longitude,
                        "shop_latitude": temp_product.shop_latitude,
                        "shop_address": temp_product.shop_address,
                    }
                ],
                "deliveries": [
                ]
            }

            # Colors
            colors = str(request.data.get('product_color')).split(',')
            colors = Colors.objects.filter(code_color__in=colors)
            product_colors = []
            for color in colors:
                temp_product.product_color.add(color.pk)
                product_colors.append(
                    {
                        "pk": color.pk,
                        "code_color": color.code_color,
                        "name_color": color.name_color
                    }
                )
            data['product_colors'] = product_colors

            # Sizes
            sizes = str(request.data.get('product_size')).split(',')
            sizes = Sizes.objects.filter(code_size__in=sizes)
            product_sizes = []
            for size in sizes:
                temp_product.product_size.add(size.pk)
                product_sizes.append(
                    {
                        "pk": size.pk,
                        "code_color": size.code_size,
                        "name_color": size.name_size
                    }
                )
            data['product_size'] = product_sizes

            # Categories
            categories = str(request.data.get('product_categories')).split(',')
            categories = Categories.objects.filter(code_category__in=categories)
            product_categories = []
            for category in categories:
                temp_product.product_category.add(category.pk)
                product_categories.append(
                    {
                        "pk": category.pk,
                        "code_category": category.code_category,
                        "name_category": category.name_category
                    }
                )
            data['product_categories'] = product_categories

            # ForWhom
            for_whom = str(request.data.get('for_whom')).split(',')
            for_whom = ForWhom.objects.filter(code_for_whom__in=for_whom)
            product_for_whom = []
            for for_who in for_whom:
                temp_product.for_whom.add(for_who.pk)
                product_for_whom.append(
                    {
                        "pk": for_who.pk,
                        "code_for_whom": for_who.code_size,
                        "name_for_whom": for_who.name_size
                    }
                )
            data['for_whom'] = product_for_whom

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

                cities = Cities.objects.filter(pk__in=cities)
                delivery_cities_1 = []
                for city in cities:
                    delivery_cities_1.append(
                        {
                            "pk": city.pk,
                            "city_en": city.city_en,
                            "city_fr": city.city_fr,
                            "city_ar": city.city_ar
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

                cities = Cities.objects.filter(pk__in=cities)
                delivery_cities_2 = []
                for city in cities:
                    delivery_cities_2.append(
                        {
                            "pk": city.pk,
                            "city_en": city.city_en,
                            "city_fr": city.city_fr,
                            "city_ar": city.city_ar
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

                cities = Cities.objects.filter(pk__in=cities)
                delivery_cities_3 = []
                for city in cities:
                    delivery_cities_3.append(
                        {
                            "pk": city.pk,
                            "city_en": city.city_en,
                            "city_fr": city.city_fr,
                            "city_ar": city.city_ar
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
                        'temp_product': temp_product_pk,
                        'temp_delivery_city': delivery_cities_1_pk,
                        'temp_delivery_price': int(delivery_price_1),
                        'temp_delivery_days': int(delivery_days_1)
                    }
                )
            if delivery_city_2:
                city_2_check = True
                deliveries.append(
                    {
                        'temp_product': temp_product_pk,
                        'temp_delivery_city': delivery_cities_2_pk,
                        'temp_delivery_price': int(delivery_price_2),
                        'temp_delivery_days': int(delivery_days_2)
                    }
                )
            if delivery_city_3:
                city_3_check = True
                deliveries.append(
                    {
                        'temp_product': temp_product_pk,
                        'temp_delivery_city': delivery_cities_3_pk,
                        'temp_delivery_price': int(delivery_price_3),
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
            return Response(data=data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        temp_product_pk = request.data.get('id_temp_product')
        try:
            temp_product = TempProduct.objects.get(pk=temp_product_pk)
            picture_1 = request.data.get('picture_1', None)
            picture_2 = request.data.get('picture_2', None)
            picture_3 = request.data.get('picture_3', None)
            picture_4 = request.data.get('picture_4', None)

            previous_images = list()
            previous_images.append(API_URL + temp_product.picture_1.url
                                   if temp_product.picture_1 else False)
            previous_images.append(API_URL + temp_product.picture_2.url
                                   if temp_product.picture_2 else False)
            previous_images.append(API_URL + temp_product.picture_3.url
                                   if temp_product.picture_3 else False)
            previous_images.append(API_URL + temp_product.picture_4.url
                                   if temp_product.picture_4 else False)

            if isinstance(picture_1, InMemoryUploadedFile):
                try:
                    picture_1_path = self.parent_file_dir + temp_product.picture_1.url
                    picture_1_thumb_path = self.parent_file_dir + temp_product.picture_1_thumbnail.url
                    remove(picture_1_path)
                    remove(picture_1_thumb_path)
                except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                    pass
                temp_product.picture_1 = None
                temp_product.save()
            else:
                # src
                if picture_1 in previous_images:
                    try:
                        img_1_index = previous_images.index(picture_1)
                        if img_1_index == 0:
                            picture_1 = temp_product.picture_1
                        elif img_1_index == 1:
                            picture_1 = temp_product.picture_2
                        elif img_1_index == 2:
                            picture_1 = temp_product.picture_3
                        else:
                            picture_1 = temp_product.picture_4
                    # None wasn't sent
                    except ValueError:
                        picture_1 = None

            if isinstance(picture_2, InMemoryUploadedFile):
                try:
                    picture_2_path = self.parent_file_dir + temp_product.picture_2.url
                    picture_2_thumb_path = self.parent_file_dir + temp_product.picture_2_thumbnail.url
                    remove(picture_2_path)
                    remove(picture_2_thumb_path)
                except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                    pass
                temp_product.picture_2 = None
                temp_product.save()
            else:
                # src
                if picture_2 in previous_images:
                    try:
                        img_2_index = previous_images.index(picture_2)
                        if img_2_index == 0:
                            picture_2 = temp_product.picture_2
                        elif img_2_index == 1:
                            picture_2 = temp_product.picture_2
                        elif img_2_index == 2:
                            picture_2 = temp_product.picture_2
                        else:
                            picture_2 = temp_product.picture_2
                    # None wasn't sent
                    except ValueError:
                        picture_2 = None

            if isinstance(picture_3, InMemoryUploadedFile):
                try:
                    picture_3_path = self.parent_file_dir + temp_product.picture_3.url
                    picture_3_thumb_path = self.parent_file_dir + temp_product.picture_3_thumbnail.url
                    remove(picture_3_path)
                    remove(picture_3_thumb_path)
                except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                    pass
                temp_product.picture_3 = None
                temp_product.save()
            else:
                # src
                if picture_3 in previous_images:
                    try:
                        img_3_index = previous_images.index(picture_3)
                        if img_3_index == 0:
                            picture_3 = temp_product.picture_3
                        elif img_3_index == 1:
                            picture_3 = temp_product.picture_3
                        elif img_3_index == 2:
                            picture_3 = temp_product.picture_3
                        else:
                            picture_3 = temp_product.picture_3
                    # None wasn't sent
                    except ValueError:
                        picture_3 = None

            if isinstance(picture_4, InMemoryUploadedFile):
                try:
                    picture_4_path = self.parent_file_dir + temp_product.picture_4.url
                    picture_4_thumb_path = self.parent_file_dir + temp_product.picture_4_thumbnail.url
                    remove(picture_4_path)
                    remove(picture_4_thumb_path)
                except (FileNotFoundError, SuspiciousFileOperation, ValueError, AttributeError):
                    pass
                temp_product.picture_4 = None
                temp_product.save()
            else:
                # src
                if picture_4 in previous_images:
                    try:
                        img_4_index = previous_images.index(picture_4)
                        if img_4_index == 0:
                            picture_4 = temp_product.picture_4
                        elif img_4_index == 1:
                            picture_4 = temp_product.picture_4
                        elif img_4_index == 2:
                            picture_4 = temp_product.picture_4
                        else:
                            picture_4 = temp_product.picture_4
                    # None wasn't sent
                    except ValueError:
                        picture_4 = None

            # Temp product PUT serializer
            temp_product_serializer = TempProductPutSerializer(data={
                'product_name': request.data.get('product_name', ''),
                'picture_1': picture_1,
                'picture_2': picture_2,
                'picture_3': picture_3,
                'picture_4': picture_4,
                'description': request.data.get('description', ''),
                'quantity': request.data.get('quantity', ''),
                'price': request.data.get('price', ''),
                'price_by': request.data.get('price_by', ''),
                'shop_longitude': request.data.get('shop_longitude', ''),
                'shop_latitude': request.data.get('shop_latitude', ''),
                'shop_address': request.data.get('shop_address', ''),
            })
            if temp_product_serializer.is_valid():
                temp_updated_product = temp_product_serializer.update(temp_product,
                                                                      temp_product_serializer.validated_data)
                # Edit categories
                temp_product.product_category.clear()
                categories = str(request.data.get('product_categories')).split(',')
                new_categories = Categories.objects.filter(code_category__in=categories)
                product_categories = []
                for category in new_categories:
                    temp_product.product_category.add(category.pk)
                    product_categories.append(
                        {
                            "pk": category.pk,
                            "code_category": category.code_category,
                            "name_category": category.name_category
                        }
                    )
                # Edit colors
                temp_product.product_color.clear()
                colors = str(request.data.get('product_color')).split(',')
                new_colors = Colors.objects.filter(code_color__in=colors)
                product_colors = []
                for color in new_colors:
                    temp_product.product_color.add(color.pk)
                    product_colors.append(
                        {
                            "pk": color.pk,
                            "code_color": color.code_color,
                            "name_color": color.name_color
                        }
                    )
                # Edit sizes
                temp_product.product_size.clear()
                sizes = str(request.data.get('product_size')).split(',')
                new_sizes = Sizes.objects.filter(code_size__in=sizes)
                product_sizes = []
                for size in new_sizes:
                    temp_product.product_size.add(size.pk)
                    product_sizes.append(
                        {
                            "pk": size.pk,
                            "code_size": size.code_size,
                            "name_size": size.name_size
                        }
                    )
                # Edit for_whom
                temp_product.for_whom.clear()
                for_whom = str(request.data.get('for_whom')).split(',')
                for_whom = ForWhom.objects.filter(code_for_whom__in=for_whom)
                product_for_whom = []
                for for_who in for_whom:
                    temp_product.for_whom.add(for_who.pk)
                    product_for_whom.append(
                        {
                            "pk": for_who.pk,
                            "code_for_whom": for_who.code_size,
                            "name_for_whom": for_who.name_size
                        }
                    )
                # Edit deliveries
                temp_product.temp_delivery_temp_product.all().delete()
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

                    cities = Cities.objects.filter(pk__in=cities)
                    delivery_cities_1 = []
                    for city in cities:
                        delivery_cities_1.append(
                            {
                                "pk": city.pk,
                                "city_en": city.city_en,
                                "city_fr": city.city_fr,
                                "city_ar": city.city_ar
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

                    cities = Cities.objects.filter(pk__in=cities)
                    delivery_cities_2 = []
                    for city in cities:
                        delivery_cities_2.append(
                            {
                                "pk": city.pk,
                                "city_en": city.city_en,
                                "city_fr": city.city_fr,
                                "city_ar": city.city_ar
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

                    cities = Cities.objects.filter(pk__in=cities)
                    delivery_cities_3 = []
                    for city in cities:
                        delivery_cities_3.append(
                            {
                                "pk": city.pk,
                                "city_en": city.city_en,
                                "city_fr": city.city_fr,
                                "city_ar": city.city_ar
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
                            'temp_product': temp_product_pk,
                            'temp_delivery_city': delivery_cities_1_pk,
                            'temp_delivery_price': int(delivery_price_1),
                            'temp_delivery_days': int(delivery_days_1)
                        }
                    )
                if delivery_city_2:
                    city_2_check = True
                    deliveries.append(
                        {
                            'temp_product': temp_product_pk,
                            'temp_delivery_city': delivery_cities_2_pk,
                            'temp_delivery_price': int(delivery_price_2),
                            'temp_delivery_days': int(delivery_days_2)
                        }
                    )
                if delivery_city_3:
                    city_3_check = True
                    deliveries.append(
                        {
                            'temp_product': temp_product_pk,
                            'temp_delivery_city': delivery_cities_3_pk,
                            'temp_delivery_price': int(delivery_price_3),
                            'temp_delivery_days': int(delivery_days_3)
                        }
                    )

                # Save edited deliveries
                deliveries_list = []
                delivery_serializer = BaseTempShopDeliverySerializer(data=deliveries, many=True)
                if delivery_serializer.is_valid():
                    # Delete old deliveries cities
                    TempDelivery.objects.filter(temp_product__pk=temp_product_pk).delete()
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
                    deliveries_list = deliveries
                if temp_product.picture_1:
                    temp_product.picture_1 = self.rename_product_pictures(temp_product.picture_1)
                    temp_product.save()
                if temp_product.picture_2:
                    temp_product.picture_2 = self.rename_product_pictures(temp_product.picture_2)
                    temp_product.save()
                if temp_product.picture_3:
                    temp_product.picture_3 = self.rename_product_pictures(temp_product.picture_3)
                    temp_product.save()
                if temp_product.picture_4:
                    temp_product.picture_4 = self.rename_product_pictures(temp_product.picture_4)
                    temp_product.save()
                temp_product_pk = temp_product.pk
                # Generate thumbnails
                base_generate_product_thumbnails.apply_async((temp_product_pk,), )
                # Returned data
                data = {
                    "pk": temp_updated_product.pk,
                    "picture_1": temp_updated_product.get_absolute_picture_1_img,
                    "picture_1_thumb": temp_updated_product.get_absolute_picture_1_thumbnail,
                    "picture_2": temp_updated_product.get_absolute_picture_2_img,
                    "picture_2_thumb": temp_updated_product.get_absolute_picture_2_thumbnail,
                    "picture_3": temp_updated_product.get_absolute_picture_3_img,
                    "picture_3_thumb": temp_updated_product.get_absolute_picture_3_thumbnail,
                    "picture_4": temp_updated_product.get_absolute_picture_4_img,
                    "picture_4_thumb": temp_updated_product.get_absolute_picture_4_thumbnail,
                    "product_name": temp_updated_product.product_name,
                    "store_name": temp_updated_product.temp_shop.shop_name,
                    "product_categories": product_categories,
                    "description": temp_updated_product.description,
                    "for_whom": product_for_whom,
                    "product_color": product_colors,
                    "product_size": product_sizes,
                    "price": temp_updated_product.price,
                    "price_by": temp_updated_product.price_by,
                    "click_and_collect": [
                        {
                            "shop_longitude": temp_updated_product.shop_longitude,
                            "shop_latitude": temp_updated_product.shop_latitude,
                            "shop_address": temp_updated_product.shop_address,
                        }
                    ],
                    "deliveries": deliveries_list
                }
                return Response(data, status=status.HTTP_200_OK)
            return Response(temp_product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except TempProduct.DoesNotExist:
            data = {'errors': ['Temp product not found.']}
            return Response(data=data, status=status.HTTP_404_NOT_FOUND)


class GetOneTempProductView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        try:
            temp_product = TempProduct.objects.get(pk=product_id)
            temp_product_details_serializer = BaseTempProductDetailsSerializer(temp_product)
        except TempProduct.DoesNotExist:
            data = {'errors': ['Temp product not found.']}
            return Response(data=data, status=status.HTTP_404_NOT_FOUND)
        return Response(temp_product_details_serializer.data, status=status.HTTP_200_OK)


class GetTempShopProductsListView(APIView, PaginationMixinBy5):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        unique_id = kwargs.get('unique_id')
        try:
            temp_shop = TempShop.objects.get(unique_id=unique_id)
            temp_shop_products = TempProduct.objects.filter(temp_shop=temp_shop).order_by('-created_date')
            page = self.paginate_queryset(queryset=temp_shop_products)
            if page is not None:
                serializer = BaseTempProductsListSerializer(instance=page, many=True)
                return self.get_paginated_response(serializer.data)
            data = {'response': 'Temp shop has no products.'}
            return Response(data=data, status=status.HTTP_200_OK)
        except TempProduct.DoesNotExist:
            data = {'errors': ['Temp shop unique_id not found.']}
            return Response(data=data, status=status.HTTP_404_NOT_FOUND)


class TempShopSolderView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        temp_product_id = kwargs.get('temp_product_id')
        try:
            temp_solder = TempSolder.objects.get(temp_product=temp_product_id)
            temp_product_details_serializer = BaseTempShopSolderSerializer(temp_solder)
        except TempSolder.DoesNotExist:
            data = {'errors': ['Temp product solder not found.']}
            return Response(data=data, status=status.HTTP_404_NOT_FOUND)
        return Response(temp_product_details_serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def post(request, *args, **kwargs):
        temp_product_id = request.data.get('temp_product_id')
        temp_product = TempProduct.objects.get(pk=temp_product_id).pk
        serializer = BaseTempShopSolderSerializer(data={
            'temp_product': temp_product,
            'temp_solder_type': request.data.get('temp_solder_type'),
            'temp_solder_value': request.data.get('temp_solder_value'),
        })
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def put(request, *args, **kwargs):
        temp_product_id = request.data.get('temp_product_id')
        temp_solder = TempSolder.objects.get(temp_product=temp_product_id)
        serializer = BaseTempShopSolderPutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(temp_solder, serializer.validated_data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        data = {}
        temp_product_id = kwargs.get('temp_product_id')
        try:
            TempSolder.objects.get(temp_product=temp_product_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TempSolder.DoesNotExist:
            data['errors'] = ["Temp product solder not found."]
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
