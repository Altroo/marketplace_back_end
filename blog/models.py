from uuid import uuid4
# from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.db.models import Model
from django.contrib.postgres.fields import ArrayField
from Qaryb_API.settings import API_URL
from os import path


def get_blog_imgs_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('blog/', str(uuid4()) + file_extension)


class Blog(Model):
    page_url = models.SlugField(verbose_name='Page url (unique)', max_length=255, blank=True, null=True,
                                unique=True, default=None)
    background_image = models.ImageField(verbose_name='Background image',
                                         upload_to=get_blog_imgs_path, blank=True, null=True,
                                         default=None)
    background_image_alt = models.CharField(verbose_name="Description de l'image", max_length=255,
                                            blank=True, null=True, default=None)
    title = models.CharField(verbose_name='Titre de la page', max_length=255,
                             blank=True, null=True, default=None)
    tags = ArrayField(models.CharField(verbose_name='Tags', max_length=100,
                                       blank=True, null=True, default=None),
                      default=None, blank=True, null=True, size=None, help_text='Separated by comma ","')
    header = models.TextField(verbose_name='Titre (h1)', blank=True, null=True, default=None)
    page_meta_description = models.TextField(verbose_name='Meta description',
                                             blank=True, null=True, default=None)
    content = RichTextUploadingField(config_name='blog_editor', verbose_name='Page content',
                                     blank=True, null=True, default=None)
    indexed = models.BooleanField(verbose_name='Page publier ?', default=True)
    created_date = models.DateTimeField(verbose_name='Created date',
                                        editable=False, auto_now_add=True, db_index=True)

    # background_image = RichTextUploadingField(verbose_name='Background image', config_name='background_uploader',
    #                                               blank=True, null=True, default=None)

    def __str__(self):
        return '{} - {}'.format(self.title, self.page_url)

    @property
    def get_absolute_background_img(self):
        if self.background_image:
            return "{0}{1}".format(API_URL, self.background_image.url)
        return None

    class Meta:
        verbose_name = 'Blog page'
        verbose_name_plural = 'Blog pages'
        ordering = ('-pk',)
