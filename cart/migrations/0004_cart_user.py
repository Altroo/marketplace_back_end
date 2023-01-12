# Generated by Django 4.1.5 on 2023-01-10 21:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cart', '0003_alter_cart_options_alter_cart_picked_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='user',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_cart', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]
