# Generated by Django 4.1.4 on 2022-12-13 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0006_alter_orderdetails_product_latitude_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderdetails',
            name='picked_quantity',
            field=models.PositiveIntegerField(blank=True, default=None, null=True, verbose_name='Quantity'),
        ),
    ]
