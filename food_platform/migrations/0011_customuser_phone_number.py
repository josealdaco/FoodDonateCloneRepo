# Generated by Django 3.1.1 on 2020-09-17 01:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food_platform', '0010_auto_20200916_2337'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='phone_number',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]