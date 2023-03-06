# Generated by Django 4.1.5 on 2023-03-06 15:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportScheme',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('importer', models.CharField(editable=False, max_length=255)),
                ('importer_hash', models.CharField(editable=False, max_length=32)),
                ('status', models.IntegerField(choices=[(0, 'New'), (1, 'File Received')], default=0)),
                ('public', models.BooleanField(default=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportSchemeFile',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('status', models.IntegerField(choices=[(0, 'New'), (1, 'Uploaded'), (2, 'Inspecting'), (3, 'Inspected'), (4, 'Importing'), (5, 'Imported')], default=0)),
                ('import_scheme', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='ml_import_wizard.importscheme')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportSchemeItem',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('added_date', models.DateField(auto_now_add=True)),
                ('updated_date', models.DateField(auto_now=True)),
                ('import_scheme', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='items', to='ml_import_wizard.importscheme')),
                ('import_scheme_item', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='items', to='ml_import_wizard.importschemeitem')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportSchemeFileField',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('sample', models.TextField(blank=True, null=True)),
                ('import_scheme_file', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='ml_import_wizard.importschemefile')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
