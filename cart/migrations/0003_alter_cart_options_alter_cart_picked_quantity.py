# Generated by Django 4.1.4 on 2022-12-13 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0002_alter_cart_unique_together_cart_unique_id_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cart',
            options={'ordering': ('-updated_date', '-created_date'), 'verbose_name': 'Cart', 'verbose_name_plural': 'Carts'},
        ),
        migrations.AlterField(
            model_name='cart',
            name='picked_quantity',
            field=models.PositiveIntegerField(blank=True, default=None, null=True, verbose_name='Quantity'),
        ),
    ]
