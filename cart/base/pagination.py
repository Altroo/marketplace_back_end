from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
from cart.base.models import Cart
from offer.base.models import Solder
from cart.base.serializers import BaseSingleCartOneOrMultiOffersSerializer


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

    def get_paginated_response_custom(self, datas, cart_shop_count, total_price):
        # Manual serialzer
        # One or multiple offers from one or multiple shops.
        # CASE 1 (dynamic includes case 1.1 & 1.2 from quiver)
        if cart_shop_count > 1:
            results = []
            clean_results = []
            results_dict = {}
            clean_results_dict = {}

            for cart_offer in datas:
                results_dict['shop_pk'] = cart_offer.offer.auth_shop.pk
                results_dict['shop_picture'] = cart_offer.offer.auth_shop.get_absolute_avatar_thumbnail
                results_dict['shop_name'] = cart_offer.offer.auth_shop.shop_name
                results_dict['offer_title'] = cart_offer.offer.title
                results_dict['offer_price'] = self.get_offer_price(cart_offer)
                results_dict['id_offers'] = cart_offer.offer.pk
                result_dict = OrderedDict(results_dict)
                results.append(result_dict)
                results_dict.clear()

            for result in results:
                shop_pk = result['shop_pk']
                query = Cart.objects.filter(user=self.request.user, offer__auth_shop=shop_pk)
                offer_ids = list(query.values_list('offer_id', flat=True))
                offers_len = len(query)
                offer_prices = 0
                for offer in query:
                    offer_prices += self.get_offer_price(offer)
                cart_ids = list(query.values_list('pk', flat=True))
                clean_results_dict['shop_pk'] = shop_pk
                clean_results_dict['shop_picture'] = result['shop_picture']
                clean_results_dict['shop_name'] = result['shop_name']
                if offers_len == 1:
                    title_value = result['offer_title']
                    offer_price = result['offer_price']
                else:
                    title_value = "{} articles".format(offers_len)
                    offer_price = offer_prices
                clean_results_dict['offer_title'] = title_value
                clean_results_dict['offer_price'] = offer_price
                clean_results_dict['id_offers'] = offer_ids
                clean_results_dict['offers_count'] = offers_len
                clean_results_dict['cart_ids'] = cart_ids
                clean_result = OrderedDict(clean_results_dict)
                if clean_result not in clean_results:
                    clean_results.append(clean_result)
                clean_results_dict.clear()

            return Response(OrderedDict([
                ('count', self.page.paginator.count),
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
                ('total_price', total_price),
                ('results', clean_results)
            ]))
        else:
            # One or multiple offers from one shop.
            # CASE 2
            page = self.paginate_queryset(request=self.request, queryset=datas)
            if page is not None:
                serializer = BaseSingleCartOneOrMultiOffersSerializer(instance=page, many=True,
                                                                      context={'total_price': total_price})
                return self.get_paginated_response(serializer.data)
