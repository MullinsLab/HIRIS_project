# Generated by Django 4.1.5 on 2023-06-04 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_rename_pubmed_id_publication_publication_pubmed_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='integration',
            name='integration_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
