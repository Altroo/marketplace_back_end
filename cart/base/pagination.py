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

    def get_paginated_response_custom(self, datas, shop_count, total_price):
        # Manual serialzer
        if shop_count > 1:
            results = []
            shop_pks = set()
            for cart_offer in datas:
                results_dict = {}
                details_list = []
                shops = Cart.objects.filter(offer__auth_shop__pk=cart_offer.offer.auth_shop.pk)
                results_dict['offers_count'] = shops.count()
                results_dict['shop_pk'] = cart_offer.offer.auth_shop.pk
                shop_pks.add(cart_offer.offer.auth_shop.pk)
                results_dict['shop_picture'] = cart_offer.offer.auth_shop.get_absolute_avatar_thumbnail
                results_dict['shop_name'] = cart_offer.offer.auth_shop.shop_name
                query = Cart.objects.filter(user=self.request.user, offer__auth_shop=results_dict['shop_pk'])
                offer_prices = 0
                for offer in query:
                    offer_prices += GetCartPrices().get_offer_price(offer)
                results_dict['offers_total_price'] = offer_prices
                # Details
                for i in shops:
                    details_dict = {'cart_pk': i.pk, 'offer_pk': i.offer.pk,
                                    'offer_picture': i.offer.get_absolute_picture_1_thumbnail,
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
                if offers_len > 1:
                    i['shop_name'] = "{} articles".format(offers_len)
                clean_results.append(i)

            # One or multiple offers from one or multiple shops.
            return Response(OrderedDict([
                ('shops_count', len(shop_pks)),
                ('total_offers_count', self.page.paginator.count),
                ('total_price', total_price),
                ('results', clean_results),
            ]))
        else:
            # One or multiple offers from one shop.
            # CASE 2
            page = self.paginate_queryset(request=self.request, queryset=datas)
            if page is not None:
                serializer = BaseSingleCartOneOrMultiOffersSerializer(instance=page, many=True,
                                                                      context={'total_price': total_price})
                shop_count = 0
                if serializer.data:
                    shop_count = 1
                return Response(OrderedDict([
                    ('shops_count', shop_count),
                    ('total_offers_count', self.page.paginator.count),
                    ('total_price', total_price),
                    ('results', serializer.data)
                ]))


class GetCartOffersDetailsPagination(PageNumberPagination):

    @staticmethod
    def get_offer_price(instance, offer_type):
        try:
            solder = Solder.objects.get(offer=instance.offer.pk)
            # Réduction fix
            if solder.solder_type == 'F':
                offer_price = instance.offer.price - solder.solder_value
            # Réduction Pourcentage
            else:
                offer_price = instance.offer.price - (instance.offer.price * solder.solder_value / 100)
            if offer_type == 'V':
                return offer_price * instance.picked_quantity
            else:
                return offer_price
        except Solder.DoesNotExist:
            if offer_type == 'V':
                return instance.offer.price * instance.picked_quantity
            else:
                return instance.offer.price

    def get_paginated_response_custom(self, user, shop_pk, total_price):
        results_list = []
        # Check for Lot 1
        offer_pks = Cart.objects.filter(user=user, offer__auth_shop=shop_pk) \
            .order_by('-created_date', '-updated_date') \
            .values_list("offer__pk", flat=True).all()
        # Excludings deliveries means getting only the ones with click & collect and only products
        product_offers = Cart.objects.filter(offer_id__in=offer_pks) \
            .order_by('-created_date', '-updated_date') \
            .exclude(offer__offer_type='S')
        click_and_collect_offers = product_offers.exclude(offer__offer_delivery__isnull=False)
        lot_1 = False
        lot_2 = False
        lot_1_pks_to_exclude = []
        if click_and_collect_offers:
            details_dict = {}
            lot_1_list = []
            offres_dict = {}
            product_longitude = ''
            product_latitude = ''
            product_address = ''
            for i in click_and_collect_offers:
                lot_1_pks_to_exclude.append(i.pk)
                product_longitude = i.offer.offer_products.product_longitude
                product_latitude = i.offer.offer_products.product_latitude
                product_address = i.offer.offer_products.product_address
                lot_1_dict = {
                    "cart_pk": i.pk,
                    "offer_pk": i.offer.pk,
                    "offer_picture": i.offer.get_absolute_picture_1_thumbnail,
                    "offer_title": i.offer.title,
                    "offer_price": self.get_offer_price(i, 'V'),
                    "offer_details": {
                        "offer_max_quantity": i.offer.offer_products.product_quantity,
                        "picked_color": i.picked_color,
                        "picked_size": i.picked_size,
                        "picked_quantity": i.picked_quantity
                    }
                }
                lot_1_list.append(lot_1_dict)
            click_and_collect = {
                "product_longitude": product_longitude,
                "product_latitude": product_latitude,
                "product_address": product_address,
            }
            offres_dict['cart_details'] = lot_1_list
            offres_dict['click_and_collect'] = click_and_collect

            # Lot 1
            details_dict["Lot"] = offres_dict
            lot_1 = True
            results_list.append(details_dict)

        # Check for Lot 2
        click_and_collect_deliveries_offers = product_offers.exclude(pk__in=lot_1_pks_to_exclude)
        if click_and_collect_deliveries_offers:
            details_dict = {}
            lot_1_list = []
            offres_dict = {}
            product_longitude = ''
            product_latitude = ''
            product_address = ''
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
                    "offer_picture": i.offer.get_absolute_picture_1_thumbnail,
                    "offer_title": i.offer.title,
                    "offer_price": self.get_offer_price(i, 'V'),
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

            click_and_collect = {
                "product_longitude": product_longitude,
                "product_latitude": product_latitude,
                "product_address": product_address,
            }
            offres_dict['cart_details'] = lot_1_list
            offres_dict['click_and_collect'] = click_and_collect
            sorted_deliveries = sorted(deliveries_output, key=lambda item: item['delivery_price'])
            offres_dict['deliveries'] = sorted_deliveries

            # Append to Lot 1, 2 if exists
            if lot_1:
                lot_2 = True
                # lot 2
                details_dict["Lot"] = offres_dict
            else:
                lot_1 = True
                lot_2 = False
                # lot 1
                details_dict["Lot"] = offres_dict
            results_list.append(details_dict)
        # Check for Lot 3
        # Excludings products
        services_offers = Cart.objects.filter(offer_id__in=offer_pks) \
            .order_by('-created_date', '-updated_date') \
            .exclude(offer__offer_type='V')
        if services_offers:
            lot_3_list = []
            details_dict = {}
            offres_dict = {}
            for i in services_offers:
                lot_3_dict = {
                    "cart_pk": i.pk,
                    "offer_pk": i.offer.pk,
                    "offer_picture": i.offer.get_absolute_picture_1_thumbnail,
                    "offer_title": i.offer.title,
                    "offer_price": self.get_offer_price(i, 'S'),
                    "offer_details": {
                        "picked_date": i.picked_date,
                        "picked_hour": i.picked_hour,
                    }
                }
                lot_3_list.append(lot_3_dict)

            offres_dict['cart_details'] = lot_3_list

            # Append to Lot 1, 2, 3 if exists
            if lot_2:
                # lot 3
                details_dict["Lot"] = offres_dict
            else:
                if lot_1:
                    # lot 2
                    details_dict["Lot"] = offres_dict
                else:
                    # lot 1
                    details_dict["Lot"] = offres_dict
            results_list.append(details_dict)
        # Append Lot 2 to Lot 1 check if lot_1 = True
        return Response(OrderedDict([
            ('offers_count', self.page.paginator.count),
            ('total_price', total_price),
            ('results', results_list),
        ]))
