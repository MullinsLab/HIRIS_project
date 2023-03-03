# Generated by Django 4.1.5 on 2023-03-03 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('import_wizard', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportFileField',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='importfile',
            name='status',
            field=models.IntegerField(choices=[(0, 'New'), (1, 'Uploaded'), (2, 'Inspecting'), (3, 'Inspected'), (4, 'Importing'), (5, 'Imported')], default=0),
        ),
    ]
