# Generated by Django 4.2.7 on 2023-12-28 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_rename_name_userbankaccount_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserShareMoney',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_id', models.IntegerField(unique=True)),
                ('share_money', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
            ],
        ),
    ]
