# Generated by Django 4.1.5 on 2023-05-30 17:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_sampledata_unique_together_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('publication_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('pubmed_id', models.IntegerField(null=True)),
                ('data_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publications', to='core.dataset')),
            ],
            options={
                'db_table': 'publications',
            },
        ),
        migrations.CreateModel(
            name='PublicationData',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('publication_data_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('key', models.CharField(max_length=255)),
                ('value', models.JSONField()),
                ('publication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publication_data', to='core.publication')),
            ],
            options={
                'db_table': 'publication_data',
            },
        ),
        migrations.AddIndex(
            model_name='publicationdata',
            index=models.Index(fields=['key'], name='publication_key_654ad5_idx'),
        ),
        migrations.AddIndex(
            model_name='publicationdata',
            index=models.Index(fields=['publication', 'key'], name='publication_publica_e9c9ed_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='publicationdata',
            unique_together={('publication', 'key')},
        ),
        migrations.AlterUniqueTogether(
            name='publication',
            unique_together={('data_set', 'pubmed_id')},
        ),
    ]
