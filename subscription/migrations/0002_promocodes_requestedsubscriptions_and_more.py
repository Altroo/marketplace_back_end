# Generated by Django 4.1 on 2022-10-20 18:25

from django.db import migrations, models
import django.db.models.deletion
import subscription.models


class Migration(migrations.Migration):

    dependencies = [
        ('places', '0001_initial'),
        ('shop', '0012_alter_authshop_latitude_alter_authshop_longitude'),
        ('subscription', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PromoCodes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('promo_code', models.CharField(max_length=6, unique=True, verbose_name='Promo code')),
                ('type_promo_code', models.CharField(choices=[('P', 'Price'), ('S', 'Slots')], default='P', max_length=1, verbose_name='Type promo code')),
                ('usage_unique', models.BooleanField(default=False, verbose_name='Usage unique')),
                ('value', models.PositiveIntegerField(verbose_name='-% price or nbr (depend on type)')),
                ('promo_code_status', models.CharField(choices=[('V', 'Valid'), ('E', 'Expired')], default='V', max_length=1, verbose_name='Promo code status')),
            ],
            options={
                'verbose_name': 'Promo code',
                'verbose_name_plural': 'Promo codes',
                'ordering': ('-pk',),
            },
        ),
        migrations.CreateModel(
            name='RequestedSubscriptions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.CharField(blank=True, max_length=30, null=True, verbose_name='Company')),
                ('ice', models.CharField(blank=True, max_length=15, null=True, verbose_name='ICE')),
                ('first_name', models.CharField(max_length=30, verbose_name='First name')),
                ('last_name', models.CharField(max_length=30, verbose_name='Last name')),
                ('adresse', models.CharField(max_length=30, verbose_name='Adresse')),
                ('city', models.CharField(max_length=30, verbose_name='City')),
                ('code_postal', models.CharField(max_length=30, verbose_name='Code postal')),
                ('payment_type', models.CharField(choices=[('C', 'Carte'), ('V', 'Virement')], default='C', max_length=1, verbose_name='Payment type')),
                ('reference_number', models.CharField(max_length=255, unique=True, verbose_name='Reference number')),
                ('status', models.CharField(choices=[('A', 'Accepted'), ('R', 'Rejected'), ('P', 'Processing')], default='P', max_length=1, verbose_name='Status')),
                ('created_date', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Order date')),
                ('updated_date', models.DateTimeField(auto_now=True, verbose_name='Updated date')),
                ('auth_shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auth_shop_requested_subscription', to='shop.authshop', verbose_name='Auth Shop')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='country_requested_subscription', to='places.country', verbose_name='Country')),
                ('promo_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='promo_code_requested_subscription', to='subscription.promocodes', verbose_name='Applied Promo code')),
            ],
            options={
                'verbose_name': 'Requested subscription',
                'verbose_name_plural': 'Requested subscriptions',
                'ordering': ('-pk',),
            },
        ),
        migrations.RemoveField(
            model_name='availablesubscription',
            name='prix_unitaire',
        ),
        migrations.AddField(
            model_name='availablesubscription',
            name='prix_unitaire_ht',
            field=models.PositiveIntegerField(blank=True, default=None, null=True, verbose_name="Prix d'article HT/article"),
        ),
        migrations.AddField(
            model_name='availablesubscription',
            name='prix_unitaire_ttc',
            field=models.PositiveIntegerField(blank=True, default=None, null=True, verbose_name="Prix d'article TTC/article"),
        ),
        migrations.AlterField(
            model_name='availablesubscription',
            name='pourcentage',
            field=models.IntegerField(blank=True, default=None, null=True, verbose_name='Réduction pourcentage'),
        ),
        migrations.AlterField(
            model_name='availablesubscription',
            name='prix_ht',
            field=models.PositiveIntegerField(blank=True, default=None, null=True, verbose_name='Prix abonnement HT/ans'),
        ),
        migrations.AlterField(
            model_name='availablesubscription',
            name='prix_ttc',
            field=models.PositiveIntegerField(blank=True, default=None, null=True, verbose_name='Prix abonnement TTC/ans'),
        ),
        migrations.CreateModel(
            name='SubscribedUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('available_slots', models.PositiveIntegerField(blank=True, default=None, null=True, verbose_name='Available slots')),
                ('total_paid', models.PositiveIntegerField(blank=True, default=None, null=True, verbose_name='Total paid TTC/ans')),
                ('facture', models.FilePathField(path='media/files/562314fc-2e6d-4f77-b2a8-9072c518be36.pdf', verbose_name='Facture')),
                ('expiration_date', models.DateTimeField(default=subscription.models.get_expiration_date, verbose_name='Expiration date')),
                ('original_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='original_request_subscribed_users', to='subscription.requestedsubscriptions', verbose_name='Original subscription')),
            ],
            options={
                'verbose_name': 'Subscribed user',
                'verbose_name_plural': 'Subscribed users',
                'ordering': ('-pk',),
            },
        ),
        migrations.AddField(
            model_name='requestedsubscriptions',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_requested_subscription', to='subscription.availablesubscription', verbose_name='Subscription picked'),
        ),
    ]