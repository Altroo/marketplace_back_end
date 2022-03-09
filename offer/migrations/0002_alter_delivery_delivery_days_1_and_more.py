# Generated by Django 4.0.3 on 2022-03-09 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='delivery',
            name='delivery_days_1',
            field=models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Number of Days 1'),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='delivery_days_2',
            field=models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Number of Days 2'),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='delivery_days_3',
            field=models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Number of Days 3'),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='delivery_price_1',
            field=models.FloatField(blank=True, default=0.0, null=True, verbose_name='Delivery Price 1'),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='delivery_price_2',
            field=models.FloatField(blank=True, default=0.0, null=True, verbose_name='Delivery Price 2'),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='delivery_price_3',
            field=models.FloatField(blank=True, default=0.0, null=True, verbose_name='Delivery Price 3'),
        ),
    ]
