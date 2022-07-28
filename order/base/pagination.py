from enum import Enum

from django.db.models import QuerySet
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

from order.models import OrderDetails, Order


class GetMyOrderDetailsPagination(PageNumberPagination):

    @staticmethod
    def get_initiator_name_and_pk(order_type, order):
        if order_type == "buy":
            try:
                return order.seller.shop_name, order.seller.pk
            except AttributeError:
                return order.shop_name, order.seller.pk
        else:
            try:
                return order.buyer.first_name + ' ' + order.buyer.last_name, order.buyer.pk
            except AttributeError:
                return order.first_name + ' ' + order.last_name, order.buyer.pk

    @staticmethod
    def mark_order_as_viewed(order_type, order):
        if order_type == 'buy':
            order.viewed_buyer = True
            order.save()
        else:
            order.viewed_seller = True
            order.save()

    def get_paginated_response_custom(self, order: Order, order_details: QuerySet[OrderDetails], total_price: float,
                                      order_type: Enum('buy', 'sell')):
        results_list = []
        click_and_collect_orders = order_details.filter(picked_click_and_collect=True)
        lot_1 = False
        lot_2 = False
        lot_1_pks_to_exclude = []
        if click_and_collect_orders:
            details_dict = {}
            lot_1_list = []
            orders_dict = {}
            product_longitude = ''
            product_latitude = ''
            product_address = ''
            total_self_price = 0
            for i in click_and_collect_orders:
                total_self_price += i.total_self_price
                lot_1_pks_to_exclude.append(i.pk)
                product_longitude = i.product_longitude
                product_latitude = i.product_latitude
                product_address = i.product_address
                lot_1_dict = {
                    "pk": i.pk,
                    "picture": i.get_absolute_offer_thumbnail,
                    "title": i.title,
                    "price": i.total_self_price,
                    "order_status": i.order_status,
                    "offer_details": {
                        "picked_quantity": i.picked_quantity,
                        "picked_color": i.picked_color,
                        "picked_size": i.picked_size
                    }
                }
                lot_1_list.append(lot_1_dict)

            click_and_collect_orders = {
                "product_longitude": product_longitude,
                "product_latitude": product_latitude,
                "product_address": product_address,
            }

            orders_dict['order_details'] = lot_1_list
            orders_dict['click_and_collect'] = click_and_collect_orders
            orders_dict['total_price'] = total_self_price
            # orders_dict['order_status'] = total_self_price
            # Lot 1
            details_dict["Lot"] = orders_dict
            lot_1 = True
            results_list.append(details_dict)

        # Check for Lot 2
        deliveries_orders = order_details.filter(picked_delivery=True) \
            .exclude(pk__in=lot_1_pks_to_exclude)
        if deliveries_orders:
            details_dict = {}
            lot_1_list = []
            orders_dict = {}
            deliveries_obj = {
                "delivery_price": 0,
                "first_name": '',
                "last_name": '',
                "address": '',
                "city": '',
                "zip_code": '',
                "country": '',
                "phone": '',
                "email": '',
            }
            total_self_price = 0
            total_delivery_price = 0
            for i in deliveries_orders:
                total_self_price += i.total_self_price
                total_delivery_price = i.delivery_price
                lot_1_dict = {
                    "pk": i.pk,
                    "picture": i.get_absolute_offer_thumbnail,
                    "title": i.title,
                    "price": i.total_self_price,
                    "order_status": i.order_status,
                    "offer_details": {
                        "picked_quantity": i.picked_quantity,
                        "picked_color": i.picked_color,
                        "picked_size": i.picked_size
                    }
                }
                lot_1_list.append(lot_1_dict)
                if i.delivery_price > deliveries_obj["delivery_price"]:
                    deliveries_obj["delivery_price"] = i.delivery_price
                if i.first_name:
                    deliveries_obj["first_name"] = i.first_name
                if i.last_name:
                    deliveries_obj["last_name"] = i.last_name
                if i.address:
                    deliveries_obj["address"] = i.address
                if i.city:
                    deliveries_obj["city"] = i.city
                if i.zip_code:
                    deliveries_obj["zip_code"] = i.zip_code
                if i.country:
                    deliveries_obj["country"] = i.country
                if i.phone:
                    deliveries_obj["phone"] = i.phone
                if i.email:
                    deliveries_obj["email"] = i.email

            orders_dict['order_details'] = lot_1_list
            orders_dict['delivery'] = deliveries_obj
            orders_dict['total_price'] = total_self_price + total_delivery_price

            # Append to Lot 1, 2 if exists
            if lot_1:
                lot_2 = True
                # lot 2
                details_dict["Lot"] = orders_dict
            else:
                lot_1 = True
                lot_2 = False
                # lot 1
                details_dict["Lot"] = orders_dict
            results_list.append(details_dict)
        # Check for Lot 3
        # Excludings products
        services_orders = order_details.filter(offer_type='S')
        if services_orders:
            lot_3_list = []
            details_dict = {}
            orders_dict = {}
            total_self_price = 0
            buyer_infos = {
                "first_name": '',
                "last_name": '',
                "phone": '',
                "email": ''
            }
            for i in services_orders:
                total_self_price += i.total_self_price
                lot_3_dict = {
                    "pk": i.pk,
                    "picture": i.get_absolute_offer_thumbnail,
                    "title": i.title,
                    "price": i.total_self_price,
                    "order_status": i.order_status,
                    "offer_details": {
                        "picked_date": i.picked_date,
                        "picked_hour": i.picked_hour,
                    }
                }
                service_localisation = {
                    "service_zone_by": i.service_zone_by,
                    "service_longitude": i.service_longitude,
                    "service_latitude": i.service_latitude,
                    "service_address": i.service_address,
                    "service_km_radius": i.service_km_radius
                }
                if i.first_name:
                    buyer_infos["first_name"] = i.first_name
                if i.last_name:
                    buyer_infos["last_name"] = i.last_name
                if i.phone:
                    buyer_infos["phone"] = i.phone
                if i.email:
                    buyer_infos["email"] = i.email
                # lot_3_dict['buyer_infos'] = buyer_infos
                lot_3_dict['localisation'] = service_localisation
                lot_3_list.append(lot_3_dict)

            orders_dict['order_details'] = lot_3_list
            orders_dict['buyer_infos'] = buyer_infos
            orders_dict['total_price'] = total_self_price
            # Append to Lot 1, 2, 3 if exists
            if lot_2:
                # lot 3
                details_dict["Lot"] = orders_dict
            else:
                if lot_1:
                    # lot 2
                    details_dict["Lot"] = orders_dict
                else:
                    # lot 1
                    details_dict["Lot"] = orders_dict
            results_list.append(details_dict)
        # Append Lot 2 to Lot 1 check if lot_1 = True
        self.mark_order_as_viewed(order_type, order)
        user_name, user_pk = self.get_initiator_name_and_pk(order_type, order)

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('user_name', user_name),
            ('user_pk', user_pk),
            ('order_number', order.order_number),
            ('order_date', order.order_date),
            # ('order_status', order.order_status),
            ('note', order.note),
            ('total_price', total_price),
            ('results', results_list),
        ]))
