# Generated by Django 4.1.5 on 2023-05-10 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='integration',
            index=models.Index(fields=['ltr'], name='integration_ltr_341eb1_idx'),
        ),
    ]
