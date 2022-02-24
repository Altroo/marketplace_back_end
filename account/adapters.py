from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
import logging

logger = logging.getLogger(__name__)


class BaseSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_app(self, request, provider):
        # NOTE: Avoid loading models at top due to registry boot...
        from allauth.socialaccount.models import SocialApp
        # 1 added line here
        from allauth.socialaccount import app_settings
        config = app_settings.PROVIDERS.get(provider, {}).get('APP')
        app = SocialApp.objects.get_or_create(provider=provider)[0]
        app.client_id = config['client_id']
        app.secret = config['secret']
        return app

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        from os import path
        parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../.."))
        file_name = parent_file_dir + 'test.txt'
        with open(file_name, 'a+') as myfile:
            myfile.write('Facebook error! - provider id : {} - error : {} - exception : {} - extra_context : {}'
                         .format(provider_id, error.__str__(), exception.__str__(), extra_context))
        # logger.debug('Facebook error! - provider id : {} - error : {} - exception : {} - extra_context : {}'
        #             .format(provider_id, error.__str__(), exception.__str__(), extra_context))
