# Generated by Django 4.0.2 on 2022-02-22 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('temp_offer', '0002_alter_tempservices_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='tempservices',
            name='service_km_radius',
            field=models.FloatField(blank=True, default=None, null=True, verbose_name='Km radius'),
        ),
    ]
