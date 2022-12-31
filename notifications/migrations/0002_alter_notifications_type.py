# Generated by Django 4.1.4 on 2022-12-24 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notifications',
            name='type',
            field=models.CharField(blank=True, choices=[('', 'Unset'), ('SA', 'Subscription activated'), ('OR', 'Order received')], default='', max_length=2, null=True),
        ),
    ]