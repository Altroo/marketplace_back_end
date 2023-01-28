from rest_framework.pagination import PageNumberPagination
from Qaryb_API.settings import MESSAGES_TO_LOAD, CONVERSATIONS_TO_LOAD
from rest_framework.response import Response
from account.models import CustomUser
from shop.models import AuthShop
from chat.models import Status
from collections import OrderedDict
from rest_framework.exceptions import NotFound
from django.core.paginator import InvalidPage


class BaseMessagePagination(PageNumberPagination):
    page_size = MESSAGES_TO_LOAD

    def get_paginated_response(self, data):
        target = self.request.query_params.get('target', None)
        try:
            receiver = CustomUser.objects.get(pk=target)
            try:
                online_status = Status.objects.get(user=receiver).online
                online_timestamp = Status.objects.get(user=receiver).last_update
            except Status.DoesNotExist:
                online_timestamp = None
                online_status = False
            try:
                auth_shop = AuthShop.objects.get(user=target)
                # try:
                #     today_date = date.today()
                #     mode_vacance_obj = auth_shop.objects.select_related('auth_shop_mode_vacance')
                #     mode_vacance_to = mode_vacance_obj.date_to
                #     if mode_vacance_to > today_date:
                #         mode_vacance = {
                #             'mode_vacance': True,
                #             'date_to': mode_vacance_to
                #         }
                #     else:
                #         mode_vacance = {
                #             'mode_vacance': False,
                #         }
                # except auth_shop.auth_shop_mode_vacance.DoesNotExist:
                #     mode_vacance = {
                #         'mode_vacance': False,
                #     }
                shop = {
                    'shop_pk': auth_shop.pk,
                    'shop_name': auth_shop.shop_name,
                    'shop_avatar': auth_shop.get_absolute_avatar_thumbnail,
                    'shop_url': auth_shop.qaryb_link,
                    # 'mode_vacance': mode_vacance
                }
            except AuthShop.DoesNotExist:
                shop = None
            return Response({
                'receiver': {
                    'pk': receiver.pk,
                    'first_name': receiver.first_name,
                    'last_name': receiver.last_name,
                    'picture': receiver.get_absolute_avatar_thumbnail,
                    'online': online_status,
                    'online_timestamp': online_timestamp,
                    'shop': shop,
                },
                'chat_messages': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                    'count': self.page.paginator.count,
                    'results': data
                }
            })
        except CustomUser.DoesNotExist:
            pass


class BaseConversationPagination(PageNumberPagination):
    page_size = CONVERSATIONS_TO_LOAD
    #
    # def get_paginated_response(self, data):
    #     return Response(OrderedDict([
    #         ('count', self.page.paginator.count),
    #         ('next', self.get_next_link()),
    #         ('previous', self.get_previous_link()),
    #         ('results', sorted(data, key=lambda k: (k['created']), reverse=True))
    #     ]))
