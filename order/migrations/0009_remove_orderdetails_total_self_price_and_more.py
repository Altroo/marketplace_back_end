# Generated by Django 4.1.4 on 2022-12-16 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0008_rename_title_orderdetails_offer_title_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderdetails',
            name='total_self_price',
        ),
        migrations.AlterField(
            model_name='order',
            name='total_price',
            field=models.FloatField(blank=True, default=0, help_text='all offers price (total_self_price)', null=True, verbose_name='Order total price'),
        ),
    ]
