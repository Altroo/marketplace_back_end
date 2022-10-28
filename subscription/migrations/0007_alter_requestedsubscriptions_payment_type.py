# Generated by Django 4.1 on 2022-10-21 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0006_alter_subscribedusers_original_request'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestedsubscriptions',
            name='payment_type',
            field=models.CharField(choices=[('', 'Unset'), ('C', 'Carte'), ('V', 'Virement')], default='', max_length=1, verbose_name='Payment type'),
        ),
    ]
