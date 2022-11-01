from datetime import datetime
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from subscription.models import AvailableSubscription, RequestedSubscriptions, \
    PromoCodes, SubscribedUsers, get_facture_path, IndexedArticles
from subscription.base.serializers import BaseGETAvailableSubscriptionsSerializer, \
    BasePOSTRequestSubscriptionSerializer, BasePOSTSubscribedUsersSerializer, \
    BaseGETCurrentUserSubscription, BasePUTRequestSubscriptionSerializer, \
    BasePUTSubscribedUsersSerializer, BaseGETIndexedArticlesList, BaseGETAvailableArticlesList, \
    BasePOSTIndexArticlesSerializer
from shop.models import AuthShop
from places.models import Country
from offers.models import Offers
from fpdf import FPDF
from uuid import uuid4


class SubscriptionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def generate_reference_number(pk):
        date_time = datetime.now()
        time_stamp = datetime.timestamp(date_time)
        str_time_stamp = str(time_stamp)
        str_time_stamp_seconds = str_time_stamp.split('.')
        timestamp_rnd = str_time_stamp_seconds[0][6:]
        uid = urlsafe_base64_encode(force_bytes(pk))
        return '{}{}'.format(uid, timestamp_rnd)

    @staticmethod
    def generate_pdf(auth_shop, validated_data):
        # generate pdf
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(200, 10, txt='Nom boutique : ' + auth_shop.shop_name, ln=1, align='L')
        pdf.cell(200, 10, txt='Reference number : ' + validated_data.get('reference_number'), ln=2, align='L')
        base_path = get_facture_path()
        pdf_output_path = "{}{}.{}".format(base_path, uuid4(), 'pdf')
        pdf.output(pdf_output_path)
        return pdf_output_path

    @staticmethod
    def update_pdf(auth_shop, db_data):
        # generate pdf
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(200, 10, txt='Nom boutique : ' + auth_shop.shop_name, ln=1, align='L')
        pdf.cell(200, 10, txt='Reference number : ' + db_data.reference_number, ln=2, align='L')
        base_path = get_facture_path()
        pdf_output_path = "{}{}.{}".format(base_path, uuid4(), 'pdf')
        pdf.output(pdf_output_path)
        return pdf_output_path

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            nbr_article = request.data.get('nbr_article')
            company = request.data.get('company')
            ice = request.data.get('ice')
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            adresse = request.data.get('adresse')
            city = request.data.get('city')
            code_postal = request.data.get('code_postal')
            country = request.data.get('country')
            try:
                country_obj = Country.objects.get(name_fr=country)
            except Country.DoesNotExist:
                country_obj = Country.objects.get(name_fr='Maroc')  # fallback
            promo_code = request.data.get('promo_code')
            promo_code_obj = None
            try:
                promo_code_obj = PromoCodes.objects.get(promo_code=promo_code)
            except PromoCodes.DoesNotExist:
                pass
                # errors = {"error": ["Promo code non valid."]}
                # raise ValidationError(errors)
                # promo_code_obj = None
            try:
                nbr_articles_obj = AvailableSubscription.objects.get(nbr_article=nbr_article)
            except AvailableSubscription.DoesNotExist:
                errors = {"error": ["Cette formule n'existe pas."]}
                raise ValidationError(errors)
            payment_type = request.data.get('payment_type')
            reference_number = self.generate_reference_number(auth_shop.pk)
            requested_subscription_serializer = BasePOSTRequestSubscriptionSerializer(data={
                'auth_shop': auth_shop.pk,
                'subscription': nbr_articles_obj.pk,
                'company': company,
                'ice': ice,
                'first_name': first_name,
                'last_name': last_name,
                'adresse': adresse,
                'city': city,
                'code_postal': code_postal,
                'country': country_obj.pk,
                'promo_code': promo_code_obj.pk if promo_code_obj else None,
                'payment_type': payment_type,
                'reference_number': reference_number,
            })
            if requested_subscription_serializer.is_valid():
                requested_subscription = requested_subscription_serializer.save()
                validated_data = requested_subscription_serializer.validated_data
                # calculate price
                total_paid = nbr_articles_obj.prix_ttc
                available_slots = nbr_articles_obj.nbr_article
                if promo_code_obj:
                    if promo_code_obj.promo_code_status == 'E':
                        return
                    elif promo_code_obj.type_promo_code == 'S' and promo_code_obj.value is not None:
                        total_paid = 0
                        available_slots = promo_code_obj.value
                    elif promo_code_obj.type_promo_code == 'P' and promo_code_obj.value is not None:
                        total_paid = round(nbr_articles_obj.prix_ttc - promo_code_obj.value)
                pdf_output_path = self.generate_pdf(auth_shop, validated_data)
                if total_paid == 0:
                    requested_subscription.status = 'A'
                    requested_subscription.save()
                    subscribe_user_serializer = BasePOSTSubscribedUsersSerializer(data={
                        'original_request': requested_subscription.pk,
                        'available_slots': available_slots,
                        'total_paid': total_paid,
                        'facture': pdf_output_path,
                    })
                    if subscribe_user_serializer.is_valid():
                        subscribe_user_serializer.save()
                        if promo_code_obj:
                            promo_code_obj.promo_code_status = 'E'
                            promo_code_obj.save()
                        data = {
                            'reference_number': validated_data.get('reference_number'),
                            'total_paid': total_paid,
                        }
                        return Response(data=data, status=status.HTTP_200_OK)
                    else:
                        requested_subscription.delete()
                        raise ValidationError(subscribe_user_serializer.errors)
                else:
                    requested_subscription.save()
                    data = {
                        'reference_number': validated_data.get('reference_number'),
                        'total_paid': total_paid,
                    }
                    return Response(data=data, status=status.HTTP_200_OK)
            raise ValidationError(requested_subscription_serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)

    def patch(self, request, *args, **kwargs):
        user = request.user
        try:
            subscribed_user = SubscribedUsers.objects.get(original_request__auth_shop__user=user)
            nbr_article = request.data.get('nbr_article')
            company = request.data.get('company')
            ice = request.data.get('ice')
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            adresse = request.data.get('adresse')
            city = request.data.get('city')
            code_postal = request.data.get('code_postal')
            country = request.data.get('country')
            try:
                country_obj = Country.objects.get(name_fr=country)
            except Country.DoesNotExist:
                country_obj = Country.objects.get(name_fr='Maroc')  # fallback
            # promo_code = request.data.get('promo_code')
            # try:
            #     promo_code_obj = PromoCodes.objects.get(promo_code=promo_code)
            # except PromoCodes.DoesNotExist:
            #     errors = {"error": ["Promo code non valid."]}
            #     raise ValidationError(errors)
            #     # promo_code_obj = None
            try:
                nbr_articles_obj = AvailableSubscription.objects.get(nbr_article=nbr_article)
            except AvailableSubscription.DoesNotExist:
                errors = {"error": ["Cette formule n'existe pas."]}
                raise ValidationError(errors)
            payment_type = request.data.get('payment_type')
            requested_subscription_serializer = BasePUTRequestSubscriptionSerializer(
                subscribed_user.original_request,
                data={
                    'subscription': nbr_articles_obj.pk,
                    'company': company,
                    'ice': ice,
                    'first_name': first_name,
                    'last_name': last_name,
                    'adresse': adresse,
                    'city': city,
                    'code_postal': code_postal,
                    'country': country_obj.pk,
                    # 'promo_code': promo_code_obj.pk if promo_code_obj else None,
                    'promo_code': None,
                    'payment_type': payment_type,
                }, partial=True)
            if requested_subscription_serializer.is_valid():
                # days remain * (new price / 365) = final price.
                previous_expiration_date = subscribed_user.expiration_date
                remaining_days = previous_expiration_date - timezone.now()
                final_price = remaining_days.days * (nbr_articles_obj.prix_ttc / 365)
                total_paid = subscribed_user.total_paid + round(final_price)
                available_slots = nbr_articles_obj.nbr_article + subscribed_user.available_slots
                # Todo - add promo code type upgrade
                # if promo_code_obj:
                #     if promo_code_obj.promo_code_status == 'E':
                #         return
                #     elif promo_code_obj.type_promo_code == 'S' and promo_code_obj.value is not None:
                #         total_paid = subscribed_user.total_paid + final_price
                #         available_slots = promo_code_obj.value + subscribed_user.available_slots
                #     elif promo_code_obj.type_promo_code == 'P' and promo_code_obj.value is not None:
                #         total_paid = round(nbr_articles_obj.prix_ttc - promo_code_obj.value) + \
                #                      subscribed_user.total_paid
                requested_subscription = requested_subscription_serializer.save()
                pdf_output_path = self.update_pdf(subscribed_user.original_request.auth_shop, requested_subscription)

                subscribe_user_serializer = BasePUTSubscribedUsersSerializer(subscribed_user, data={
                    'available_slots': available_slots,
                    'total_paid': total_paid,
                    'facture': pdf_output_path,
                }, partial=True)
                if subscribe_user_serializer.is_valid():
                    subscribe_user_serializer.save()
                    requested_subscription.status = 'P'
                    requested_subscription.save()
                    # TODO : enable once test is done
                    # if promo_code_obj:
                    #     promo_code_obj.promo_code_status = 'E'
                    #     promo_code_obj.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    requested_subscription.delete()
                    raise ValidationError(subscribe_user_serializer.errors)
            raise ValidationError(requested_subscription_serializer.errors)
        except SubscribedUsers.DoesNotExist:
            errors = {"error": ["Subscription not found."]}
            raise ValidationError(errors)

    @staticmethod
    def get(request, *args, **kwargs):
        nbr_article = kwargs.get('nbr_article')
        try:
            subscription = AvailableSubscription.objects.get(nbr_article=nbr_article)
        except AvailableSubscription.DoesNotExist:
            data = {"error": ["Cette formule n'existe pas."]}
            raise ValidationError(data)
        serializer = BaseGETAvailableSubscriptionsSerializer(subscription)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


# Create your views here.
class AvailableSubscriptionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        available_subscriptions = AvailableSubscription.objects.all().order_by('pk')
        serializer = BaseGETAvailableSubscriptionsSerializer(available_subscriptions, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class GetUserSubscriptionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        try:
            subscribed_user = SubscribedUsers.objects.get(original_request__auth_shop__user=user)
            serializer = BaseGETCurrentUserSubscription(subscribed_user)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except SubscribedUsers.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PromoCodeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        promo_code = request.data.get('promo_code')
        data = {
            'validity': False,
            'type': None,
            'value': None,
        }
        try:
            promo_code_obj = PromoCodes.objects.get(promo_code=promo_code)
            if promo_code_obj.promo_code_status == 'E':
                # return expired
                return Response(data=data, status=status.HTTP_200_OK)
            elif promo_code_obj.promo_code_status == 'V':
                # else check if valid but expiration date passed - mark as expired and return false
                if promo_code_obj.expiration_date is not None:
                    if promo_code_obj.expiration_date < timezone.now():
                        promo_code_obj.promo_code_status = 'E'
                        promo_code_obj.save()
                        return Response(data=data, status=status.HTTP_200_OK)
                data['validity'] = True
                data['type'] = promo_code_obj.type_promo_code
                data['value'] = promo_code_obj.value
            return Response(data=data, status=status.HTTP_200_OK)
        except PromoCodes.DoesNotExist:
            return Response(data=data, status=status.HTTP_200_OK)


class GetUserIndexedArticlesView(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)
    page_size = 10

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            indexed_offers = IndexedArticles.objects.filter(offer__auth_shop__user=user)
            page = self.paginate_queryset(request=request, queryset=indexed_offers)
            if page is not None:
                serializer = BaseGETIndexedArticlesList(page, many=True)
                return self.get_paginated_response(serializer.data)
        except SubscribedUsers.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def post(request, *args, **kwargs):
        user = request.user
        offer_ids: str = request.data.get('offer_ids')
        try:
            subscribed_user = SubscribedUsers.objects.get(original_request__auth_shop__user=user)
            ids_to_index = offer_ids.split(',')
            already_indexed_articles = IndexedArticles.objects.filter(offer__auth_shop__user=user)\
                .values_list('offer__pk', flat=True)
            user_offers = Offers.objects.filter(auth_shop__user=user, pk__in=ids_to_index)\
                .exclude(pk__in=already_indexed_articles)
            if (already_indexed_articles.count() + user_offers.count()) <= subscribed_user.available_slots:
                data = []
                for offer in user_offers:
                    index_article = {
                        'subscription': subscribed_user.pk,
                        'offer': offer.pk,
                    }
                    data.append(index_article)
                serializer = BasePOSTIndexArticlesSerializer(data=data, many=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                raise ValidationError(serializer.errors)
            else:
                errors = {"error": ["Pas assez de slots."]}
                raise ValidationError(errors)
        except SubscribedUsers.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, *args, **kwargs):
        user = request.user
        indexed_article_pk = kwargs.get('indexed_article_pk')
        indexed_articles_pks_list = str(indexed_article_pk).split(',')
        indexed_articles = IndexedArticles.objects.filter(offer__auth_shop__user=user,
                                                          pk__in=indexed_articles_pks_list)
        indexed_articles.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetUserAvailableArticlesView(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)
    page_size = 10

    def get(self, request, *args, **kwargs):
        user = request.user
        indexed_offers = IndexedArticles.objects.filter(offer__auth_shop__user=user)\
            .values_list('offer__pk', flat=True)
        remaining_offers = Offers.objects.filter(auth_shop__user=user).exclude(pk__in=indexed_offers)
        page = self.paginate_queryset(request=request, queryset=remaining_offers)
        if page is not None:
            serializer = BaseGETAvailableArticlesList(page, many=True)
            return self.get_paginated_response(serializer.data)