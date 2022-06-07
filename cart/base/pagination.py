from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
from cart.models import Cart
from offers.models import Solder
from cart.base.serializers import BaseSingleCartOneOrMultiOffersSerializer


# class GetMyCartPagination(PageNumberPagination):
#
#     @staticmethod
#     def get_offer_price(instance):
#         try:
#             solder = Solder.objects.get(offer=instance.offer.pk)
#             # Réduction fix
#             if solder.solder_type == 'F':
#                 offer_price = instance.offer.price - solder.solder_value
#             # Réduction Pourcentage
#             else:
#                 offer_price = instance.offer.price - (instance.offer.price * solder.solder_value / 100)
#             return offer_price * instance.picked_quantity
#         except Solder.DoesNotExist:
#             return instance.offer.price * instance.picked_quantity
#
#     def get_paginated_response_custom(self, datas, cart_shop_count, total_price):
#         # Manual serialzer
#         # One or multiple offers from one or multiple shops.
#         if cart_shop_count > 1:
#             results = []
#             clean_results = []
#             results_dict = {}
#             clean_results_dict = {}
#
#             for cart_offer in datas:
#                 results_dict['shop_pk'] = cart_offer.offer.auth_shop.pk
#                 results_dict['shop_picture'] = cart_offer.offer.auth_shop.get_absolute_avatar_thumbnail
#                 results_dict['shop_name'] = cart_offer.offer.auth_shop.shop_name
#                 results_dict['offer_title'] = cart_offer.offer.title
#                 results_dict['offer_price'] = self.get_offer_price(cart_offer)
#                 results_dict['id_offers'] = cart_offer.offer.pk
#                 result_dict = OrderedDict(results_dict)
#                 results.append(result_dict)
#                 results_dict.clear()
#
#             for result in results:
#                 shop_pk = result['shop_pk']
#                 query = Cart.objects.filter(user=self.request.user, offer__auth_shop=shop_pk)
#                 offer_ids = list(query.values_list('offer_id', flat=True))
#                 offers_len = len(query)
#                 offer_prices = 0
#                 for offer in query:
#                     offer_prices += self.get_offer_price(offer)
#                 cart_ids = list(query.values_list('pk', flat=True))
#                 clean_results_dict['shop_pk'] = shop_pk
#                 clean_results_dict['shop_picture'] = result['shop_picture']
#                 clean_results_dict['shop_name'] = result['shop_name']
#                 if offers_len == 1:
#                     title_value = result['offer_title']
#                     offer_price = result['offer_price']
#                 else:
#                     title_value = "{} articles".format(offers_len)
#                     offer_price = offer_prices
#                 clean_results_dict['offer_title'] = title_value
#                 clean_results_dict['offer_price'] = offer_price
#                 clean_results_dict['id_offers'] = offer_ids
#                 clean_results_dict['offers_count'] = offers_len
#                 clean_results_dict['cart_ids'] = cart_ids
#                 clean_result = OrderedDict(clean_results_dict)
#                 if clean_result not in clean_results:
#                     clean_results.append(clean_result)
#                 clean_results_dict.clear()
#
#             return Response(OrderedDict([
#                 ('count', self.page.paginator.count),
#                 ('next', self.get_next_link()),
#                 ('previous', self.get_previous_link()),
#                 ('total_price', total_price),
#                 ('results', clean_results)
#             ]))
#         else:
#             # One or multiple offers from one shop.
#             # CASE 2
#             page = self.paginate_queryset(request=self.request, queryset=datas)
#             if page is not None:
#                 serializer = BaseSingleCartOneOrMultiOffersSerializer(instance=page, many=True,
#                                                                       context={'total_price': total_price})
#                 return self.get_paginated_response(serializer.data)


class GetMyCartPagination(PageNumberPagination):

    @staticmethod
    def get_offer_price(instance):
        try:
            solder = Solder.objects.get(offer=instance.offer.pk)
            # Réduction fix
            if solder.solder_type == 'F':
                offer_price = instance.offer.price - solder.solder_value
            # Réduction Pourcentage
            else:
                offer_price = instance.offer.price - (instance.offer.price * solder.solder_value / 100)
            return offer_price * instance.picked_quantity
        except Solder.DoesNotExist:
            return instance.offer.price * instance.picked_quantity

    def get_paginated_response_custom(self, datas, shop_count, total_price):
        # Manual serialzer
        # One or multiple offers from one or multiple shops.
        if shop_count > 1:
            results = []
            for cart_offer in datas:
                results_dict = {}
                details_list = []
                shops = Cart.objects.filter(offer__auth_shop__pk=cart_offer.offer.auth_shop.pk)
                results_dict['offers_count'] = shops.count()
                results_dict['shop_pk'] = cart_offer.offer.auth_shop.pk
                results_dict['shop_picture'] = cart_offer.offer.auth_shop.get_absolute_avatar_thumbnail
                results_dict['shop_name'] = cart_offer.offer.auth_shop.shop_name
                query = Cart.objects.filter(user=self.request.user, offer__auth_shop=results_dict['shop_pk'])
                offer_prices = 0
                for offer in query:
                    offer_prices += self.get_offer_price(offer)
                results_dict['offers_total_price'] = offer_prices
                # Details
                for i in shops:
                    details_dict = {'cart_pk': i.pk, 'offer_pk': i.offer.pk,
                                    'offer_picture': i.offer.get_absolute_picture_1_thumbnail,
                                    'offer_title': i.offer.title, 'offer_price': i.offer.price}
                    # Product
                    if i.offer.offer_type == 'V':
                        details_dict['offer_max_quantity'] = i.offer.offer_products.product_quantity
                        details_dict['picked_color'] = i.picked_color
                        details_dict['picked_size'] = i.picked_size
                        details_dict['picked_quantity'] = i.picked_quantity
                        if results_dict['offers_count'] == 1:
                            if i.offer.offer_products.product_longitude and i.offer.offer_products.product_latitude \
                                    and i.offer.offer_products.product_address:
                                details_dict['click_and_collect'] = {
                                    "product_longitude": i.offer.offer_products.product_longitude,
                                    "product_latitude": i.offer.offer_products.product_latitude,
                                    "product_address": i.offer.offer_products.product_address
                                }
                            if i.offer.offer_delivery:
                                deliveries_list = []
                                for delivery in i.offer.offer_delivery.all():
                                    deliveries_dict = {
                                        "delivery_city": delivery.delivery_city.values_list('name_fr', flat=True).all(),
                                        "delivery_price": delivery.delivery_price,
                                        "delivery_days": delivery.delivery_days,
                                    }
                                    deliveries_list.append(deliveries_dict)
                                details_dict['deliveries'] = deliveries_list
                    # Service
                    else:
                        details_dict['picked_date'] = i.picked_date
                        details_dict['picked_hour'] = i.picked_hour
                    # if details_dict not in details_list:
                    details_list.append(details_dict)
                    results_dict['details'] = details_list
                if results_dict not in results:
                    results.append(results_dict)

            clean_results = []
            for i in results:
                offers_len = len(i['details'])
                if offers_len > 1:
                    i['shop_name'] = "{} articles".format(offers_len)
                clean_results.append(i)

            return Response(OrderedDict([
                ('count', self.page.paginator.count),
                ('total_price', total_price),
                ('results', clean_results),
                # ('results', results)
            ]))
        else:
            # One or multiple offers from one shop.
            # CASE 2
            page = self.paginate_queryset(request=self.request, queryset=datas)
            if page is not None:
                serializer = BaseSingleCartOneOrMultiOffersSerializer(instance=page, many=True,
                                                                      context={'total_price': total_price})
                return Response(OrderedDict([
                    ('count', self.page.paginator.count),
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
                    "offer_price": self.get_offer_price(i, 'V')
                }
                product_details = {
                    "offer_max_quantity": i.offer.offer_products.product_quantity,
                    "picked_color": i.picked_color,
                    "picked_size": i.picked_size,
                    "picked_quantity": i.picked_quantity
                }
                lot_1_dict['offer_details'] = product_details
                lot_1_list.append(lot_1_dict)
            click_and_collect = {
                "product_longitude": product_longitude,
                "product_latitude": product_latitude,
                "product_address": product_address,
            }
            offres_dict['offres'] = lot_1_list
            offres_dict['click_and_collect'] = click_and_collect

            # Append to Lot 1
            details_dict["Lot N°1"] = offres_dict
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
                    "offer_price": self.get_offer_price(i, 'V')
                }
                product_details = {
                    "offer_max_quantity": i.offer.offer_products.product_quantity,
                    "picked_color": i.picked_color,
                    "picked_size": i.picked_size,
                    "picked_quantity": i.picked_quantity
                }
                lot_1_dict['offer_details'] = product_details
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

            mixed_cities_deliveries_days = list(zip(list_of_cities, list_of_prices, list_of_days,
                                                    list_of_deliveries_pks))
            deliveries = {}
            for d in mixed_cities_deliveries_days:
                if d[0] not in deliveries:
                    deliveries[d[0]] = {'price': d[1], 'days': d[2], 'delivery_pk': d[3]}
                else:
                    if deliveries[d[0]]['price'] < d[1]:
                        deliveries[d[0]]['price'] = d[1]
                        deliveries[d[0]]['delivery_pk'] = d[3]
                    if deliveries[d[0]]['days'] < d[2]:
                        deliveries[d[0]]['days'] = d[2]
                        deliveries[d[0]]['delivery_pk'] = d[3]

            unique_shifts = {}
            for key, val in deliveries.items():
                if str(val) not in unique_shifts.keys():
                    unique_shifts[str(val)] = len(deliveries_output)
                    deliveries_output.append(
                        {
                            "pk": val['delivery_pk'],
                            "cities": [str(key)],
                            "price": val['price'],
                            "days": val['days']
                        }
                    )
                else:
                    deliveries_output[unique_shifts[str(val)]]["cities"].append(str(key))

            click_and_collect = {
                "product_longitude": product_longitude,
                "product_latitude": product_latitude,
                "product_address": product_address,
            }
            offres_dict['offres'] = lot_1_list
            offres_dict['click_and_collect'] = click_and_collect
            sorted_deliveries = sorted(deliveries_output, key=lambda item: item['price'])
            offres_dict['deliveries'] = sorted_deliveries

            # Append to Lot 1, 2 if exists
            if lot_1:
                lot_2 = True
                details_dict["Lot N°2"] = offres_dict
            else:
                lot_1 = True
                lot_2 = False
                details_dict["Lot N°1"] = offres_dict
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
                    "offer_price": self.get_offer_price(i, 'S')
                }
                service_details = {
                    "picked_date": i.picked_date,
                    "picked_hour": i.picked_hour,
                }
                lot_3_dict['offer_details'] = service_details
                lot_3_list.append(lot_3_dict)

            offres_dict['offres'] = lot_3_list

            # Append to Lot 1, 2, 3 if exists
            if lot_2:
                details_dict["Lot N°3"] = offres_dict
            else:
                if lot_1:
                    details_dict["Lot N°2"] = offres_dict
                else:
                    details_dict["Lot N°1"] = offres_dict
            results_list.append(details_dict)
        # Append Lot 2 to Lot 1 check if lot_1 = True
        # TO ADD Exclude click & collect ids from the ones with deliveries

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_price', total_price),
            ('results', results_list),
        ]))
