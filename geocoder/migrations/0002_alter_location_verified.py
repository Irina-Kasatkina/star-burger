# Generated by Django 3.2.15 on 2022-11-09 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geocoder', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='verified',
            field=models.DateField(auto_now_add=True, db_index=True, verbose_name='дата запроса к геокодеру'),
        ),
    ]
