from allauth.account.utils import perform_login
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
import logging
from account.models import CustomUser
logger = logging.getLogger(__name__)


class BaseSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        if user.id:
            return
        try:
            customer = CustomUser.objects.get(email=user.email)
            sociallogin.state['process'] = 'connect'
            perform_login(request, customer, 'none')
        except CustomUser.DoesNotExist:
            pass

    # def get_app(self, request, provider, config=None):
    #     # NOTE: Avoid loading models at top due to registry boot...
    #     from allauth.socialaccount.models import SocialApp
    #     # 1 added line here
    #     from allauth.socialaccount import app_settings
    #     config = app_settings.PROVIDERS.get(provider, {}).get('APP')
    #     app = SocialApp.objects.get_or_create(provider=provider)[0]
    #     app.client_id = config['client_id']
    #     app.secret = config['secret']
    #     print(app)
    #     return app

    def get_app(self, request, provider, config=None):
        # NOTE: Avoid loading models at top due to registry boot...
        from allauth.socialaccount.models import SocialApp
        # 1 added line here
        from allauth.socialaccount import app_settings
        config = config or app_settings.PROVIDERS.get(provider, {}).get('APP')
        if config:
            app = SocialApp.objects.get_or_create(provider=provider)[0]
            for field in ["client_id", "secret", "key", "certificate_key"]:
                setattr(app, field, config.get(field))
        else:
            app = SocialApp.objects.get_current(provider, request)
        return app

    # def get_app(self, request, provider, config=None):
    #     # NOTE: Avoid loading models at top due to registry boot...
    #     from allauth.socialaccount.models import SocialApp
    #
    #     config = config or app_settings.PROVIDERS.get(provider, {}).get("APP")
    #     if config:
    #         app = SocialApp(provider=provider)
    #         for field in ["client_id", "secret", "key", "certificate_key"]:
    #             setattr(app, field, config.get(field))
    #     else:
    #         app = SocialApp.objects.get_current(provider, request)
    #     return app

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        logger.warning('Facebook error! - provider id : {} - error : {} - exception : {} - extra_context : {}'
                       .format(provider_id, error.__str__(), exception.__str__(), extra_context))
