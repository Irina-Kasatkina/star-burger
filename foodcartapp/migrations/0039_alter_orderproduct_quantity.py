# Generated by Django 3.2.15 on 2022-11-01 14:45

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0038_customer_order_orderproduct'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderproduct',
            name='quantity',
            field=models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Количество'),
        ),
    ]
