# Generated by Django 4.1.6 on 2023-02-10 19:10

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0025_alter_requestedsignins_creneau_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestedsignins',
            name='unique_number',
            field=models.CharField(default=uuid.uuid4, max_length=255, verbose_name='Unique number'),
        ),
    ]