# Generated by Django 4.1.5 on 2023-05-30 19:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_publication_publicationdata_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subject',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='subject',
            name='publication',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='core.dataset'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='integrationlocation',
            name='feature_locations',
            field=models.ManyToManyField(editable=False, related_name='integration_locations', through='core.IntegrationFeature', to='core.featurelocation'),
        ),
        migrations.AlterUniqueTogether(
            name='subject',
            unique_together={('publication', 'subject_identifier')},
        ),
        migrations.RemoveField(
            model_name='subject',
            name='data_set',
        ),
    ]