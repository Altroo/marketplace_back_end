from offers.models import Solder


class GetCartPrices:

    @classmethod
    def get_offer_price(cls, instance):
        try:
            solder = Solder.objects.get(offer=instance.offer.pk)
            # Réduction fix
            if solder.solder_type == 'F':
                offer_price = instance.offer.price - solder.solder_value
            # Réduction Pourcentage
            else:
                offer_price = instance.offer.price - (instance.offer.price * solder.solder_value / 100)
            if instance.picked_quantity:
                return offer_price * instance.picked_quantity
            else:
                return offer_price
        except Solder.DoesNotExist:
            if instance.picked_quantity:
                return instance.offer.price * instance.picked_quantity
            else:
                return instance.offer.price

    @classmethod
    def calculate_total_price(cls, cart_offers):
        total_price = 0
        for cart_offer in cart_offers:
            try:
                solder = Solder.objects.get(offer=cart_offer.offer.pk)
                # Réduction fix
                if solder.solder_type == 'F':
                    offer_price = cart_offer.offer.price - solder.solder_value
                # Réduction Pourcentage
                else:
                    offer_price = cart_offer.offer.price - (cart_offer.offer.price * solder.solder_value / 100)
                if cart_offer.picked_quantity:
                    total_price += offer_price * cart_offer.picked_quantity
                else:
                    total_price += offer_price
            except Solder.DoesNotExist:
                if cart_offer.picked_quantity:
                    total_price += cart_offer.offer.price * cart_offer.picked_quantity
                else:
                    total_price += cart_offer.offer.price
        return total_price
