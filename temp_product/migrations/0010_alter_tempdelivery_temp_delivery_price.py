# Generated by Django 4.0.2 on 2022-02-13 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('temp_product', '0009_alter_tempproduct_picture_1_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tempdelivery',
            name='temp_delivery_price',
            field=models.FloatField(default=0.0, verbose_name='Temp delivery Price'),
        ),
    ]
