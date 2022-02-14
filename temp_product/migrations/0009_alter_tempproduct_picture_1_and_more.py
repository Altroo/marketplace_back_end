# Generated by Django 4.0.2 on 2022-02-13 10:36

from django.db import migrations, models
import temp_product.base.models


class Migration(migrations.Migration):

    dependencies = [
        ('temp_product', '0008_alter_tempproduct_picture_1_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tempproduct',
            name='picture_1',
            field=models.ImageField(blank=True, default=None, max_length=1000, null=True, upload_to=temp_product.base.models.get_shop_products_path, verbose_name='Picture 1'),
        ),
        migrations.AlterField(
            model_name='tempproduct',
            name='picture_1_thumbnail',
            field=models.ImageField(blank=True, max_length=1000, null=True, upload_to=temp_product.base.models.get_shop_products_path, verbose_name='Picture 1 thumbnail'),
        ),
        migrations.AlterField(
            model_name='tempproduct',
            name='picture_2',
            field=models.ImageField(blank=True, default=None, max_length=1000, null=True, upload_to=temp_product.base.models.get_shop_products_path, verbose_name='Picture 2'),
        ),
        migrations.AlterField(
            model_name='tempproduct',
            name='picture_2_thumbnail',
            field=models.ImageField(blank=True, max_length=1000, null=True, upload_to=temp_product.base.models.get_shop_products_path, verbose_name='Picture 2 thumbnail'),
        ),
        migrations.AlterField(
            model_name='tempproduct',
            name='picture_3',
            field=models.ImageField(blank=True, default=None, max_length=1000, null=True, upload_to=temp_product.base.models.get_shop_products_path, verbose_name='Picture 3'),
        ),
        migrations.AlterField(
            model_name='tempproduct',
            name='picture_3_thumbnail',
            field=models.ImageField(blank=True, max_length=1000, null=True, upload_to=temp_product.base.models.get_shop_products_path, verbose_name='Picture 3 thumbnail'),
        ),
        migrations.AlterField(
            model_name='tempproduct',
            name='picture_4',
            field=models.ImageField(blank=True, default=None, max_length=1000, null=True, upload_to=temp_product.base.models.get_shop_products_path, verbose_name='Picture 4'),
        ),
        migrations.AlterField(
            model_name='tempproduct',
            name='picture_4_thumbnail',
            field=models.ImageField(blank=True, max_length=1000, null=True, upload_to=temp_product.base.models.get_shop_products_path, verbose_name='Picture 4 thumbnail'),
        ),
    ]
