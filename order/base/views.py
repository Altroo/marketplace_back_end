from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from auth_shop.base.models import AuthShop
from order.base.models import Order
from order.base.serializers import BaseTempOrdersListSerializer


class GetMyOrdersListView(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user_pk = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user_pk)
            temp_shop = Order.objects.filter(seller=auth_shop)
            page = self.paginate_queryset(request=request, queryset=temp_shop)
            if page is not None:
                serializer = BaseTempOrdersListSerializer(instance=page, many=True)
                return self.get_paginated_response(serializer.data)
        except AuthShop.DoesNotExist:
            data = {'errors': ['Auth shop not found.']}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
