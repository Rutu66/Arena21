# Generated by Django 4.2.14 on 2024-08-08 07:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0002_event_price_no_event_price_yes_event_quantity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='price_no',
        ),
        migrations.RemoveField(
            model_name='event',
            name='price_yes',
        ),
        migrations.RemoveField(
            model_name='event',
            name='quantity',
        ),
    ]
