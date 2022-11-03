import sys
from django.core.management import BaseCommand
from account.models import CustomUser
from account.base.tasks import start_generating_avatar_and_thumbnail, from_img_to_io


class GenerateUserImages:

    @staticmethod
    def generate_missing_images():
        users = CustomUser.objects.all()
        for user in users:
            if not user.avatar:
                last_name = str(user.last_name[0]).upper()
                first_name = str(user.first_name[0]).upper()
                avatar, thumbnail = start_generating_avatar_and_thumbnail(last_name, first_name)
                avatar_ = from_img_to_io(avatar, 'WEBP')
                thumbnail_ = from_img_to_io(thumbnail, 'WEBP')
                user.save_image('avatar', avatar_)
                user.save_image('avatar_thumbnail', thumbnail_)


class Command(BaseCommand):
    help = 'Generate missing user images'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing User images.\n')
        self.main()
        sys.stdout.write('\n')

    @staticmethod
    def main():
        class_obj = GenerateUserImages()
        try:
            class_obj.generate_missing_images()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
