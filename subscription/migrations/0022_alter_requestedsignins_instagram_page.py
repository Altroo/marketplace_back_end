# Generated by Django 4.1.5 on 2023-01-27 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0021_alter_requestedsignins_horaire'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestedsignins',
            name='instagram_page',
            field=models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='Lien de la page (instagram)'),
        ),
    ]
