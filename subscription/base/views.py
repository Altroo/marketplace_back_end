from datetime import datetime
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from subscription.models import AvailableSubscription, \
    PromoCodes, SubscribedUsers, IndexedArticles, RequestedSignIns
from subscription.base.serializers import BaseGETAvailableSubscriptionsSerializer, \
    BasePOSTRequestSubscriptionSerializer, BasePOSTSubscribedUsersSerializer, \
    BaseGETCurrentUserSubscription, \
    BaseGETIndexedArticlesList, BaseGETAvailableArticlesList, \
    BasePOSTIndexArticlesSerializer, BasePOSTRequestedSignInsSerializer
from shop.models import AuthShop
from places.models import Country
from offers.models import Offers
from notifications.models import Notifications
from subscription.base.tasks import base_generate_pdf, base_inform_new_shop_subscription, \
    append_google_sheet_row


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
        return '{}{}'.format(uid.upper(), timestamp_rnd)

    @staticmethod
    def generate_facture_number(pk):
        str_date = datetime.now().isoformat().split('T')[0].split('-')
        year = str_date[0][2:]
        month = str_date[1]
        day = str_date[2]
        uid = urlsafe_base64_encode(force_bytes(pk))
        return f'{uid.upper()}-{year}{month}{day}'

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            nbr_article = request.data.get('nbr_article')
            company = request.data.get('company', '')
            ice = request.data.get('ice', '')
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            adresse = request.data.get('adresse', '')
            city = request.data.get('city', '')
            code_postal = request.data.get('code_postal', '')
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
            facture_number = self.generate_facture_number(user.pk)

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
                    total_paid = round(total_paid - promo_code_obj.value)

            subscription_status = 'P'
            if total_paid == 0:
                # Auto accept
                subscription_status = 'A'

            requested_subscription_serializer = BasePOSTRequestSubscriptionSerializer(data={
                'status': subscription_status,
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
                'facture_number': facture_number,
            })

            if requested_subscription_serializer.is_valid():
                requested_subscription = requested_subscription_serializer.save()
                free_data = {
                    'facture_numero': facture_number,
                    'reference_number': reference_number,
                    'created_date': requested_subscription_serializer.data.get('created_date'),
                    'first_name': first_name,
                    'last_name': last_name,
                    'company': company,
                    'ice': ice,
                    'adresse': adresse,
                    'code_postal': code_postal,
                    'city': city,
                    'country': country_obj.name_fr,
                    'nbr_article': nbr_articles_obj.nbr_article,
                    'prix_ht': '0,00',
                    'tva': '0,00',
                    'prix_ttc': '0,00',
                }
                # subscribed using promo code slots, free
                if total_paid == 0:
                    subscribe_user_serializer = BasePOSTSubscribedUsersSerializer(data={
                        'original_request': requested_subscription.pk,
                        'available_slots': available_slots,
                        'total_paid': total_paid,
                    })
                    if subscribe_user_serializer.is_valid():
                        subscribe_user_serializer.save()
                        subscription = SubscribedUsers.objects.get(
                            pk=subscribe_user_serializer.data.get('pk'))
                        base_generate_pdf.apply_async((user.pk, free_data, subscription), )
                        if promo_code_obj and promo_code_obj.usage_unique:
                            promo_code_obj.promo_code_status = 'E'
                            promo_code_obj.save()
                        Notifications.objects.create(user=user, type='SA')
                        output_data = {
                            'reference_number': reference_number,
                            'total_paid': total_paid,
                        }
                        base_inform_new_shop_subscription.apply_async((auth_shop.pk, available_slots,), )
                        return Response(data=output_data, status=status.HTTP_200_OK)
                    # requested_subscription.delete()
                    raise ValidationError(subscribe_user_serializer.errors)
                # Subscribed via virement
                else:
                    # Rest of cases handled on post_save
                    output_data = {
                        'reference_number': reference_number,
                        'total_paid': total_paid,
                    }
                    return Response(data=output_data, status=status.HTTP_200_OK)
            raise ValidationError(requested_subscription_serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)

    def patch(self, request, *args, **kwargs):
        user = request.user
        try:
            auth_shop = AuthShop.objects.get(user=user)
            nbr_article = request.data.get('nbr_article')
            company = request.data.get('company', '')
            ice = request.data.get('ice', '')
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            adresse = request.data.get('adresse', '')
            city = request.data.get('city', '')
            code_postal = request.data.get('code_postal', '')
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
            facture_number = self.generate_facture_number(user.pk)
            subscribed_user = SubscribedUsers.objects.get(original_request__auth_shop__user=user)
            previous_expiration_date = subscribed_user.expiration_date
            remaining_days = previous_expiration_date - timezone.now()
            remaining_to_pay = round(remaining_days.days * (nbr_articles_obj.prix_ttc / 365))

            # calculate price
            if promo_code_obj:
                if promo_code_obj.promo_code_status == 'E' or promo_code_obj.promo_code_status == 'S':
                    return
                elif promo_code_obj.type_promo_code == 'P' and promo_code_obj.value is not None:
                    remaining_to_pay = round(remaining_to_pay - promo_code_obj.value)

            requested_subscription_serializer = BasePOSTRequestSubscriptionSerializer(data={
                'status': 'P',  # Pending for new upgrade
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
                'facture_number': facture_number,
                'remaining_to_pay': remaining_to_pay,
            })

            if requested_subscription_serializer.is_valid():
                requested_subscription_serializer.save()
                # Subscribed via virement
                # Rest of cases handled on post_receive
                output_data = {
                    'reference_number': reference_number,
                    'total_paid': remaining_to_pay,
                }
                return Response(data=output_data, status=status.HTTP_200_OK)
            raise ValidationError(requested_subscription_serializer.errors)
        except AuthShop.DoesNotExist:
            errors = {"error": ["Shop not found."]}
            raise ValidationError(errors)

    @staticmethod
    def get(request, *args, **kwargs):
        nbr_article = kwargs.get('nbr_article')
        try:
            subscription = AvailableSubscription.objects.get(nbr_article=nbr_article)
            serializer = BaseGETAvailableSubscriptionsSerializer(subscription)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except AvailableSubscription.DoesNotExist:
            data = {"error": ["Cette formule n'existe pas."]}
            raise ValidationError(data)


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
            # TODO fix duplicate
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
            # TODO fix duplicate
            subscribed_user = SubscribedUsers.objects.get(original_request__auth_shop__user=user)
            ids_to_index = offer_ids.split(',')
            already_indexed_articles = IndexedArticles.objects.filter(offer__auth_shop__user=user) \
                .values_list('offer__pk', flat=True)
            user_offers = Offers.objects.filter(auth_shop__user=user, pk__in=ids_to_index) \
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
        indexed_offers = IndexedArticles.objects.filter(offer__auth_shop__user=user) \
            .values_list('offer__pk', flat=True)
        remaining_offers = Offers.objects.filter(auth_shop__user=user).exclude(pk__in=indexed_offers)
        page = self.paginate_queryset(request=request, queryset=remaining_offers)
        if page is not None:
            serializer = BaseGETAvailableArticlesList(page, many=True)
            return self.get_paginated_response(serializer.data)


class RequestedSignInsView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        all_objects = RequestedSignIns.objects.all().count()
        name = request.data.get('name')
        phone = request.data.get('phone')
        email = request.data.get('email')
        instagram_page = request.data.get('instagram_page')
        creneau = request.data.get('creneau')
        secteur = request.data.get('secteur')
        now_date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        if creneau == '9h-12h':
            creneau_str = 'M'
        elif creneau == '13h-16h':
            creneau_str = 'A'
        else:
            creneau_str = 'S'
        serializer = BasePOSTRequestedSignInsSerializer(data={
            'name': name,
            'phone': phone,
            'instagram_page': instagram_page,
            'email': email,
            'secteur': secteur,
            'creneau': creneau_str,
        })
        if serializer.is_valid():
            serializer.save()
            # format date : 11/06/2020 10:39:09
            # insta page = link
            data = [
                [f"{now_date}", f"{name}", email, phone, instagram_page, creneau, secteur],
            ]
            ligne_number = all_objects + 18
            append_google_sheet_row.apply_async((data, ligne_number), )
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError(serializer.errors)
