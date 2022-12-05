from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
from datetime import datetime
from offers.models import OffersTotalVues


class GetMyVuesPagination(PageNumberPagination):

    def get_paginated_response_custom(self, datas, total_vues, auth_shop):
        now = datetime.now()
        this_month = datetime.now().month
        last_month = now.month - 1 if now.month > 1 else 12
        month_to_delete = now.month - 2 if now.month > 1 else 12
        # Always Delete the month before the previous one
        try:
            OffersTotalVues.objects.get(auth_shop=auth_shop, date=month_to_delete).delete()
        except OffersTotalVues.DoesNotExist:
            pass
        try:
            this_month_total_vues = OffersTotalVues.objects.get(auth_shop=auth_shop, date=this_month).nbr_total_vue
        except OffersTotalVues.DoesNotExist:
            this_month_total_vues = 0
        try:
            last_month_total_vues = OffersTotalVues.objects.get(auth_shop=auth_shop, date=last_month).nbr_total_vue
        except OffersTotalVues.DoesNotExist:
            last_month_total_vues = 0
        if last_month_total_vues != 0 and this_month_total_vues != 0:
            pourcentage = int((this_month_total_vues - last_month_total_vues) / last_month_total_vues * 100)
            if pourcentage == 0:
                pourcentage = '0%'
            elif pourcentage > 0:
                pourcentage = f'+{pourcentage}%'
            else:
                pourcentage = f'{pourcentage}%'
        else:
            pourcentage = '0%'

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('total_vues', total_vues),
            ('this_month', this_month),
            ('pourcentage', pourcentage),
            ('results', datas)
        ]))
