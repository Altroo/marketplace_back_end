# Generated by Django 4.1.5 on 2023-01-09 17:52

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_alter_blog_background_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='content',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, default=None, null=True, verbose_name='Page content'),
        ),
    ]
