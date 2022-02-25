# Generated by Django 4.0.2 on 2022-02-25 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('temp_shop', '0002_alter_tempshop_color_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tempshop',
            name='font_name',
            field=models.CharField(blank=True, choices=[('LI', 'Light'), ('BO', 'Boldy'), ('CL', 'Classic'), ('MA', 'Magazine'), ('PO', 'Pop'), ('SA', 'Sans'), ('PA', 'Pacifico'), ('FI', 'Fira')], default='L', max_length=2, null=True, verbose_name='Font name'),
        ),
    ]
