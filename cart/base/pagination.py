from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
from cart.models import Cart
from places.models import City
from offers.models import Solder
from cart.base.serializers import BaseSingleCartOneOrMultiOffersSerializer
from cart.base.utils import GetCartPrices
from django.db.models import F


class GetMyCartPagination(PageNumberPagination):

    def get_paginated_response_custom(self, datas, unique_id, shop_count, total_price):
        # Manual serialzer
        if shop_count > 1:
            results = []
            shop_pks = set()
            for cart_offer in datas:
                results_dict = {}
                details_list = []
                shops = Cart.objects.filter(offer__auth_shop__pk=cart_offer.offer.auth_shop.pk, unique_id=unique_id)
                results_dict['offers_count'] = shops.count()
                results_dict['shop_pk'] = cart_offer.offer.auth_shop.pk
                shop_pks.add(cart_offer.offer.auth_shop.pk)
                results_dict['shop_picture'] = cart_offer.offer.auth_shop.get_absolute_avatar_thumbnail
                results_dict['desktop_shop_name'] = cart_offer.offer.auth_shop.shop_name
                results_dict['shop_link'] = cart_offer.offer.auth_shop.qaryb_link
                query = Cart.objects.filter(unique_id=unique_id, offer__auth_shop=results_dict['shop_pk'])
                offer_prices = 0
                for offer in query:
                    offer_prices += GetCartPrices().get_offer_price(offer)
                results_dict['offer_total_price'] = offer_prices
                # Details
                for i in shops:
                    details_dict = {'cart_pk': i.pk, 'offer_pk': i.offer.pk,
                                    'offer_picture': i.offer.get_absolute_picture_1_thumbnail,
                                    'offer_type': i.offer.offer_type,
                                    'offer_title': i.offer.title, 'offer_price': i.offer.price, 'offer_details': {}}
                    # Product
                    if i.offer.offer_type == 'V':
                        details_dict['offer_details']['offer_max_quantity'] = i.offer.offer_products.product_quantity
                        details_dict['offer_details']['picked_color'] = i.picked_color
                        details_dict['offer_details']['picked_size'] = i.picked_size
                        details_dict['offer_details']['picked_quantity'] = i.picked_quantity

                        if results_dict['offers_count'] == 1:
                            if i.offer.offer_products.product_longitude and i.offer.offer_products.product_latitude \
                                    and i.offer.offer_products.product_address:
                                results_dict['click_and_collect'] = {
                                    "product_longitude": i.offer.offer_products.product_longitude,
                                    "product_latitude": i.offer.offer_products.product_latitude,
                                    "product_address": i.offer.offer_products.product_address
                                }

                            if i.offer.offer_delivery:
                                deliveries_list = []
                                for delivery in i.offer.offer_delivery.all():
                                    results_ = list(delivery.delivery_city.values('pk', name_=F('name_fr')).all())
                                    delivery_city = []
                                    for result in results_:
                                        delivery_city.append({
                                            'pk': result['pk'],
                                            'name': result['name_']
                                        })
                                    deliveries_dict = {
                                        "pk": delivery.pk,
                                        "delivery_city": delivery_city,
                                        "delivery_price": delivery.delivery_price,
                                        "delivery_days": delivery.delivery_days,
                                    }
                                    deliveries_list.append(deliveries_dict)
                                results_dict['deliveries'] = deliveries_list
                            # else:
                            #     results_dict['deliveries'] = None
                    # Service
                    else:
                        details_dict['offer_details']['picked_date'] = i.picked_date
                        details_dict['offer_details']['picked_hour'] = i.picked_hour
                    # if details_dict not in details_list:
                    details_list.append(details_dict)
                    results_dict['cart_details'] = details_list
                if results_dict not in results:
                    results.append(results_dict)

            clean_results = []
            for i in results:
                offers_len = len(i['cart_details'])
                plural = 's'
                if offers_len > 1:
                    i['mobile_shop_name'] = "{} article{}".format(offers_len, plural)
                elif offers_len == 1:
                    i['mobile_shop_name'] = "{} article".format(offers_len)
                clean_results.append(i)

            # One or multiple offers from one or multiple shops.
            return Response(OrderedDict([
                ('cart_type', 'MULTI_SHOP'),
                ('shops_count', len(shop_pks)),
                ('total_offers_count', self.page.paginator.count),
                ('total_price', total_price),
                ('results', results),
            ]))
        else:
            # One or multiple offers from one shop.
            # CASE 2
            page = self.paginate_queryset(request=self.request, queryset=datas)
            if page is not None:
                serializer = BaseSingleCartOneOrMultiOffersSerializer(instance=page, many=True,
                                                                      context={
                                                                          'total_price': total_price,
                                                                          'unique_id': unique_id,
                                                                      })
                shop_count = 0
                if serializer.data:
                    shop_count = 1
                return Response(OrderedDict([
                    ('cart_type', 'SINGLE_SHOP'),
                    ('shops_count', shop_count),
                    ('total_offers_count', self.page.paginator.count),
                    ('total_price', total_price),
                    ('results', serializer.data)
                ]))


class GetCartOffersDetailsPagination(PageNumberPagination):

    @staticmethod
    def get_offer_total_price(instance, offer_type):
        try:
            solder = Solder.objects.get(offer=instance.offer.pk)
            # Réduction fix
            if solder.solder_type == 'F':
                offer_price = instance.offer.price - solder.solder_value
            # Réduction Pourcentage
            else:
                offer_price = instance.offer.price - (instance.offer.price * solder.solder_value / 100)
            if offer_type == 'V':
                if instance.picked_quantity:
                    return offer_price * instance.picked_quantity
                else:
                    return offer_price
            else:
                return offer_price
        except Solder.DoesNotExist:
            if offer_type == 'V':
                if instance.picked_quantity:
                    return instance.offer.price * instance.picked_quantity
                else:
                    return instance.offer.price
            else:
                return instance.offer.price

    def get_paginated_response_custom(self, unique_id, shop_pk, total_price):
        results_list = []
        # Check for Lot 1
        offer_pks = Cart.objects.filter(unique_id=unique_id, offer__auth_shop=shop_pk) \
            .order_by('-created_date', '-updated_date') \
            .values_list("offer__pk", flat=True).all()
        # Excludings deliveries means getting only the ones with click & collect and only products
        product_offers = Cart.objects.filter(offer_id__in=offer_pks, unique_id=unique_id) \
            .order_by('-created_date', '-updated_date') \
            .exclude(offer__offer_type='S')
        click_and_collect_offers = product_offers.exclude(offer__offer_delivery__isnull=False)
        lot_1 = False
        lot_2 = False
        lot_1_pks_to_exclude = []
        # lot 1 click and collect
        if click_and_collect_offers:
            details_dict = {}
            lot_1_list = []
            offres_dict = {}
            product_longitude = False
            product_latitude = False
            product_address = False
            for i in click_and_collect_offers:
                lot_1_pks_to_exclude.append(i.pk)
                product_longitude = i.offer.offer_products.product_longitude
                product_latitude = i.offer.offer_products.product_latitude
                product_address = i.offer.offer_products.product_address
                lot_1_dict = {
                    "cart_pk": i.pk,
                    "offer_pk": i.offer.pk,
                    "shop_link": i.offer.auth_shop.qaryb_link,
                    "shop_name": i.offer.auth_shop.shop_name,
                    "offer_type": i.offer.offer_type,
                    "offer_picture": i.offer.get_absolute_picture_1_thumbnail,
                    "offer_title": i.offer.title,
                    "offer_price": self.get_offer_total_price(i, 'S'), # Using S to not calculate the quantity but only solder if exists
                    "offer_total_price": self.get_offer_total_price(i, 'V'),
                    "offer_details": {
                        "offer_max_quantity": i.offer.offer_products.product_quantity,
                        "picked_color": i.picked_color,
                        "picked_size": i.picked_size,
                        "picked_quantity": i.picked_quantity
                    }
                }
                lot_1_list.append(lot_1_dict)
            if product_longitude and product_latitude and product_address:
                click_and_collect = {
                    "product_longitude": product_longitude,
                    "product_latitude": product_latitude,
                    "product_address": product_address,
                }
                offres_dict['click_and_collect'] = click_and_collect
            else:
                offres_dict['click_and_collect'] = {}
            offres_dict['cart_details'] = lot_1_list
            offres_dict['global_offer_type'] = 'V'
            # Lot 1
            details_dict["lot"] = offres_dict
            lot_1 = True
            results_list.append(details_dict)

        # Check for Lot 2
        # deliveries + click & collect
        click_and_collect_deliveries_offers = product_offers.exclude(pk__in=lot_1_pks_to_exclude)
        if click_and_collect_deliveries_offers:
            details_dict = {}
            lot_1_list = []
            offres_dict = {}
            product_longitude = False
            product_latitude = False
            product_address = False
            list_of_deliveries_pks = []
            list_of_cities = []
            list_of_prices = []
            list_of_days = []
            deliveries_output = []
            for i in click_and_collect_deliveries_offers:
                product_longitude = i.offer.offer_products.product_longitude
                product_latitude = i.offer.offer_products.product_latitude
                product_address = i.offer.offer_products.product_address
                lot_1_dict = {
                    "cart_pk": i.pk,
                    "offer_pk": i.offer.pk,
                    "shop_link": i.offer.auth_shop.qaryb_link,
                    "shop_name": i.offer.auth_shop.shop_name,
                    "offer_type": i.offer.offer_type,
                    "offer_picture": i.offer.get_absolute_picture_1_thumbnail,
                    "offer_title": i.offer.title,
                    "offer_price": self.get_offer_total_price(i, 'S'), # Using S to not calculate the quantity but only solder if exists
                    "offer_total_price": self.get_offer_total_price(i, 'V'),
                    "offer_details": {
                        "offer_max_quantity": i.offer.offer_products.product_quantity,
                        "picked_color": i.picked_color,
                        "picked_size": i.picked_size,
                        "picked_quantity": i.picked_quantity
                    }
                }
                lot_1_list.append(lot_1_dict)
                offer_deliveries = i.offer.offer_delivery.all()
                for delivery in offer_deliveries:
                    delivery_cities = delivery.delivery_city.values_list('name_fr', flat=True).all()
                    delivery_cities_len = len(delivery_cities)
                    for delivery_city in delivery_cities:
                        list_of_cities.append(delivery_city)
                    for j in range(delivery_cities_len):
                        list_of_deliveries_pks.append(delivery.pk)
                        list_of_prices.append(delivery.delivery_price)
                        list_of_days.append(delivery.delivery_days)

            mixed_cities_deliveries_days = list(
                zip(
                    list_of_cities,
                    list_of_prices,
                    list_of_days,
                    list_of_deliveries_pks
                )
            )
            deliveries = {}
            for mixed_cities in mixed_cities_deliveries_days:
                if mixed_cities[0] not in deliveries:
                    deliveries[mixed_cities[0]] = {
                        'delivery_price': mixed_cities[1],
                        'delivery_days': mixed_cities[2],
                        'pk': mixed_cities[3]
                    }
                else:
                    if deliveries[mixed_cities[0]]['delivery_price'] < mixed_cities[1]:
                        deliveries[mixed_cities[0]]['delivery_price'] = mixed_cities[1]
                        deliveries[mixed_cities[0]]['pk'] = mixed_cities[3]
                    if deliveries[mixed_cities[0]]['delivery_days'] < mixed_cities[2]:
                        deliveries[mixed_cities[0]]['delivery_days'] = mixed_cities[2]
                        deliveries[mixed_cities[0]]['pk'] = mixed_cities[3]

            unique_shifts = {}
            cities_str = [key for (key, value) in deliveries.items()]
            cities_obj = City.objects.filter(name_fr__in=cities_str)
            for key, val in deliveries.items():
                city = cities_obj.get(name_fr=str(key))
                if str(val) not in unique_shifts.keys():
                    unique_shifts[str(val)] = len(deliveries_output)
                    delivery_city = {
                        "pk": city.pk,
                        "name": city.name_fr
                    }
                    deliveries_output.append(
                        {
                            "pk": val['pk'],
                            "delivery_city": [delivery_city],
                            "delivery_price": val['delivery_price'],
                            "delivery_days": val['delivery_days']
                        }
                    )
                else:
                    delivery_city = {
                        "pk": city.pk,
                        "name": city.name_fr
                    }
                    deliveries_output[unique_shifts[str(val)]]["delivery_city"].append(delivery_city)

            if product_longitude and product_latitude and product_address:
                click_and_collect = {
                    "product_longitude": product_longitude,
                    "product_latitude": product_latitude,
                    "product_address": product_address,
                }
                offres_dict['click_and_collect'] = click_and_collect
            else:
                offres_dict['click_and_collect'] = {}
            offres_dict['cart_details'] = lot_1_list
            offres_dict['global_offer_type'] = 'V'
            sorted_deliveries = sorted(deliveries_output, key=lambda item: item['delivery_price'])
            offres_dict['deliveries'] = sorted_deliveries

            # Append to Lot 1, 2 if exists
            if lot_1:
                lot_2 = True
                # lot 2
                details_dict["lot"] = offres_dict
            else:
                lot_1 = True
                lot_2 = False
                # lot 1
                details_dict["lot"] = offres_dict
            results_list.append(details_dict)
        # Check for Lot 3
        # Excludings products
        services_offers = Cart.objects.filter(offer_id__in=offer_pks, unique_id=unique_id) \
            .order_by('-created_date', '-updated_date') \
            .exclude(offer__offer_type='V')
        if services_offers:
            lot_3_list = []
            details_dict = {}
            offres_dict = {}
            service_longitude = False
            service_latitude = False
            service_address = False
            for i in services_offers:
                service_longitude = i.offer.offer_services.service_longitude
                service_latitude = i.offer.offer_services.service_latitude
                service_address = i.offer.offer_services.service_address
                lot_3_dict = {
                    "cart_pk": i.pk,
                    "offer_pk": i.offer.pk,
                    "shop_link": i.offer.auth_shop.qaryb_link,
                    "shop_name": i.offer.auth_shop.shop_name,
                    "offer_type": i.offer.offer_type,
                    "offer_picture": i.offer.get_absolute_picture_1_thumbnail,
                    "offer_title": i.offer.title,
                    "offer_price": self.get_offer_total_price(i, 'S'), # Using S to not calculate the quantity but only solder if exists
                    "offer_total_price": self.get_offer_total_price(i, 'S'),
                    "offer_details": {
                        "picked_date": i.picked_date,
                        "picked_hour": i.picked_hour,
                    }
                }
                lot_3_list.append(lot_3_dict)
            if service_longitude and service_latitude and service_address:
                service_coordonnee = {
                    "service_longitude": service_longitude,
                    "service_latitude": service_latitude,
                    "service_address": service_address,
                }
                offres_dict['service_coordonnee'] = service_coordonnee
            else:
                offres_dict['service_coordonnee'] = {}
            offres_dict['cart_details'] = lot_3_list
            offres_dict['global_offer_type'] = 'S'
            # Append to Lot 1, 2, 3 if exists
            if lot_2:
                # lot 3
                details_dict["lot"] = offres_dict
            else:
                if lot_1:
                    # lot 2
                    details_dict["lot"] = offres_dict
                else:
                    # lot 1
                    details_dict["lot"] = offres_dict
            results_list.append(details_dict)

        formik = ''
        if click_and_collect_offers or click_and_collect_deliveries_offers:
            formik = 'V'
        elif (not click_and_collect_offers and not click_and_collect_deliveries_offers) and services_offers:
            formik = 'S'
        # Append Lot 2 to Lot 1 check if lot_1 = True
        return Response(OrderedDict([
            ('formik', formik),
            ('offers_count', self.page.paginator.count),
            ('total_price', total_price),
            ('results', results_list),
        ]))
