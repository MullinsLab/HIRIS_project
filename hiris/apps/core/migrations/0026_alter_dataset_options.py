# Generated by Django 4.1.5 on 2024-05-14 18:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0025_dataset_groups_dataset_users"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="dataset",
            options={"ordering": ["data_set_name"]},
        ),
    ]
