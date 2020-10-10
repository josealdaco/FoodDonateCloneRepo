# Generated by Django 3.1.1 on 2020-09-15 01:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('food_platform', '0004_auto_20200915_0058'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='areas',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='UserAreas', to='food_platform.interested_area'),
        ),
    ]
