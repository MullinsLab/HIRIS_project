# Generated by Django 4.1.5 on 2023-06-04 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_integration_integration_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='sample',
            name='sample_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]