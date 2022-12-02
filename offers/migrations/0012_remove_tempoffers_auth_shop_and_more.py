# Generated by Django 4.1.2 on 2022-10-30 19:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0011_alter_offers_creator_label_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tempoffers',
            name='auth_shop',
        ),
        migrations.RemoveField(
            model_name='tempoffers',
            name='for_whom',
        ),
        migrations.RemoveField(
            model_name='tempoffers',
            name='made_in_label',
        ),
        migrations.RemoveField(
            model_name='tempoffers',
            name='offer_categories',
        ),
        migrations.RemoveField(
            model_name='tempoffers',
            name='tags',
        ),
        migrations.RemoveField(
            model_name='tempproducts',
            name='offer',
        ),
        migrations.RemoveField(
            model_name='tempproducts',
            name='product_colors',
        ),
        migrations.RemoveField(
            model_name='tempproducts',
            name='product_sizes',
        ),
        migrations.RemoveField(
            model_name='tempservices',
            name='offer',
        ),
        migrations.RemoveField(
            model_name='tempservices',
            name='service_availability_days',
        ),
        migrations.RemoveField(
            model_name='tempsolder',
            name='offer',
        ),
        migrations.DeleteModel(
            name='TempDelivery',
        ),
        migrations.DeleteModel(
            name='TempOffers',
        ),
        migrations.DeleteModel(
            name='TempProducts',
        ),
        migrations.DeleteModel(
            name='TempServices',
        ),
        migrations.DeleteModel(
            name='TempSolder',
        ),
    ]