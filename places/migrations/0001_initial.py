# Generated by Django 4.0.2 on 2022-02-03 22:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city_en', models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='City EN')),
                ('city_fr', models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='City FR')),
                ('city_ar', models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='City AR')),
            ],
            options={
                'verbose_name': 'City',
                'verbose_name_plural': 'Cities',
            },
        ),
    ]
