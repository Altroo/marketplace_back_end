from django.http import HttpRequest, HttpResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from account.models import CustomUser
from ratings.models import Ratings
from ratings.base.serializers import BaseGetRatingsListSerializer


class GetBuyingRatingsList(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user_pk = kwargs.get('user_pk')
        try:
            user = CustomUser.objects.get(pk=user_pk)
            ratings = Ratings.objects.filter(buyer=user).order_by('-created_date')
            page = self.paginate_queryset(request=request, queryset=ratings)
            if page is not None:
                serializer = BaseGetRatingsListSerializer(instance=page, many=True, context={'order_type': 'buy'})
                return self.get_paginated_response(serializer.data)
        except CustomUser.DoesNotExist:
            data = {"errors": "User doesn't exist!"}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


class GetSellingRatingsList(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user_pk = kwargs.get('user_pk')
        try:
            user = CustomUser.objects.get(pk=user_pk)
            ratings = Ratings.objects.filter(seller=user).order_by('-created_date')
            page = self.paginate_queryset(request=request, queryset=ratings)
            if page is not None:
                serializer = BaseGetRatingsListSerializer(instance=page, many=True, context={'order_type': 'sell'})
                return self.get_paginated_response(serializer.data)
        except CustomUser.DoesNotExist:
            data = {"errors": "User doesn't exist!"}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


# try:
# except Order.DoesNotExist:
#    data = {
#             "errors": "OrderDetail doesn't exist!"
#           }
#    return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

class RatingsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    # TODO rating needs to be applied on the offer
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = request.user

        # Get order_details_pk
        # Get rating note
        # Get rating body
        # check if user is seller or buyer
        # check if has_user_rating is false
        # publish rating to ratings model
        pass
