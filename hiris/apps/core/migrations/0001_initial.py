# Generated by Django 4.1.5 on 2023-04-27 16:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataSet',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('data_set_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('data_set_name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'db_table': 'data_sets',
            },
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('feature_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('feature_name', models.CharField(max_length=255, null=True)),
                ('external_gene_id', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'features',
            },
        ),
        migrations.CreateModel(
            name='FeatureLocation',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('feature_location_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('chromosome', models.CharField(max_length=255, null=True)),
                ('landmark', models.CharField(max_length=255, null=True)),
                ('feature_start', models.IntegerField()),
                ('feature_end', models.IntegerField()),
                ('feature_orientation', models.CharField(choices=[('F', 'Forward'), ('R', 'Reverse')], max_length=1)),
                ('feature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feature_locations', to='core.feature')),
            ],
            options={
                'db_table': 'feature_locations',
            },
        ),
        migrations.CreateModel(
            name='FeatureType',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('feature_type_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('feature_type_name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'db_table': 'feature_types',
            },
        ),
        migrations.CreateModel(
            name='GeneType',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('gene_type_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('gene_type_name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'db_table': 'gene_types',
            },
        ),
        migrations.CreateModel(
            name='GenomeSpecies',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('genome_species_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('genome_species_name', models.CharField(max_length=255, unique=True, verbose_name='Name of the species.')),
            ],
            options={
                'db_table': 'genome_species',
            },
        ),
        migrations.CreateModel(
            name='Integration',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('integration_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('ltr', models.CharField(choices=[('3p', '3p'), ('5p', '5p')], max_length=2, null=True)),
                ('multiple_integration', models.BooleanField(blank=True, null=True)),
                ('multiple_integration_count', models.IntegerField(blank=True, null=True)),
                ('sequence', models.TextField(blank=True, null=True)),
                ('junction_5p', models.IntegerField(blank=True, null=True)),
                ('junction_3p', models.IntegerField(blank=True, null=True)),
                ('sequence_name', models.TextField(blank=True, null=True)),
                ('sequence_uri', models.TextField(blank=True, null=True)),
                ('replicate', models.IntegerField(blank=True, null=True)),
                ('replicates', models.IntegerField(blank=True, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('data_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='integrations', to='core.dataset')),
            ],
            options={
                'db_table': 'integrations',
            },
        ),
        migrations.CreateModel(
            name='IntegrationEnvironment',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('integration_environment_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('integration_environment_name', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'integration_environments',
            },
        ),
        migrations.CreateModel(
            name='IntegrationLocation',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('integration_location_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('landmark', models.CharField(max_length=255)),
                ('location', models.IntegerField()),
                ('orientation_in_landmark', models.CharField(choices=[('F', 'Forward'), ('R', 'Reverse')], max_length=1, null=True)),
                ('feature_location', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='integration_locations', to='core.featurelocation')),
                ('integration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='integration_locations', to='core.integration')),
            ],
            options={
                'db_table': 'integration_locations',
            },
        ),
        migrations.CreateModel(
            name='Preparation',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('preparation_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('preparation_description', models.TextField(null=True)),
            ],
            options={
                'db_table': 'preparations',
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('subject_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('subject_identifier', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'subjects',
            },
        ),
        migrations.CreateModel(
            name='BlastInfo',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('integration_location', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='core.integrationlocation')),
                ('identity', models.CharField(blank=True, max_length=255, null=True)),
                ('q_start', models.IntegerField(blank=True, null=True)),
                ('gaps', models.CharField(blank=True, max_length=255, null=True)),
                ('score', models.FloatField(blank=True, null=True)),
            ],
            options={
                'db_table': 'blast_info',
            },
        ),
        migrations.CreateModel(
            name='SequencingMethod',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('sequence_method_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('sequencing_method_name', models.CharField(max_length=255, null=True)),
                ('sequencing_method_descripion', models.TextField(null=True)),
                ('preparation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sequencing_methods', to='core.preparation')),
            ],
            options={
                'db_table': 'sequencing_methods',
            },
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('sample_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('culture', models.CharField(blank=True, max_length=255, null=True)),
                ('culture_day', models.IntegerField(blank=True, null=True)),
                ('date', models.DateField(blank=True, null=True)),
                ('disease', models.CharField(blank=True, max_length=255, null=True)),
                ('genbank', models.CharField(blank=True, max_length=255, null=True)),
                ('original_id', models.CharField(blank=True, max_length=255, null=True)),
                ('provirus_activity', models.CharField(blank=True, max_length=255, null=True)),
                ('pubmed_id', models.IntegerField(blank=True, null=True)),
                ('replicates', models.IntegerField(blank=True, null=True)),
                ('tissue', models.CharField(blank=True, max_length=255, null=True)),
                ('tissue_url', models.TextField(blank=True, null=True)),
                ('type', models.CharField(blank=True, max_length=255, null=True)),
                ('visit', models.IntegerField(blank=True, null=True)),
                ('years_on_art', models.FloatField(blank=True, null=True)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples', to='core.subject')),
            ],
            options={
                'db_table': 'samples',
            },
        ),
        migrations.AddField(
            model_name='preparation',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preparations', to='core.sample'),
        ),
        migrations.AddField(
            model_name='integration',
            name='integration_environment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='integrations', to='core.integrationenvironment'),
        ),
        migrations.CreateModel(
            name='GenomeVersion',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('genome_version_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('genome_version_name', models.CharField(max_length=255, unique=True)),
                ('external_gene_id_source', models.CharField(blank=True, max_length=255, null=True)),
                ('genome_species', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='core.genomespecies')),
            ],
            options={
                'db_table': 'genome_versions',
            },
        ),
        migrations.AddField(
            model_name='feature',
            name='feature_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='features', to='core.featuretype'),
        ),
        migrations.AddField(
            model_name='feature',
            name='gene_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='features', to='core.genetype'),
        ),
        migrations.AddField(
            model_name='feature',
            name='genome_version',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='features', to='core.genomeversion'),
        ),
        migrations.CreateModel(
            name='DataSetSource',
            fields=[
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('data_set_source_id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('data_set_source_name', models.CharField(blank=True, max_length=255, null=True)),
                ('revision_data_path', models.TextField(blank=True, null=True)),
                ('revision_data_hash', models.CharField(blank=True, max_length=40, null=True)),
                ('revision_metadata_path', models.TextField(blank=True, null=True)),
                ('revision_metadata_hash', models.CharField(blank=True, max_length=40, null=True)),
                ('revision_git_hash', models.CharField(blank=True, max_length=40, null=True)),
                ('document_name', models.CharField(blank=True, max_length=250, null=True)),
                ('document_pubmed_id', models.IntegerField(blank=True, null=True)),
                ('document_uri', models.TextField(blank=True, null=True)),
                ('document_citation_url', models.TextField(blank=True, null=True)),
                ('document_citation_doi', models.TextField(blank=True, null=True)),
                ('document_citation_issn', models.CharField(blank=True, max_length=255, null=True)),
                ('document_citation_year', models.IntegerField(blank=True, null=True)),
                ('document_citation_type', models.CharField(blank=True, max_length=255, null=True)),
                ('document_citation_pages', models.CharField(blank=True, max_length=255, null=True)),
                ('document_citation_title', models.TextField(blank=True, null=True)),
                ('document_citation_author', models.TextField(blank=True, null=True)),
                ('document_citation_issue_number', models.CharField(blank=True, max_length=255, null=True)),
                ('document_citation_volume', models.IntegerField(blank=True, null=True)),
                ('document_citation_journal', models.TextField(blank=True, null=True)),
                ('document_citation_citekey', models.TextField(blank=True, null=True)),
                ('data_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_set_sources', to='core.dataset')),
            ],
            options={
                'db_table': 'data_set_sources',
            },
        ),
        migrations.AddField(
            model_name='dataset',
            name='genome_version',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_sets', to='core.genomeversion'),
        ),
        migrations.AddIndex(
            model_name='integrationlocation',
            index=models.Index(fields=['landmark', 'location'], name='integration_landmar_6e265f_idx'),
        ),
        migrations.AddIndex(
            model_name='integrationlocation',
            index=models.Index(fields=['landmark'], name='integration_landmar_bfe6d6_idx'),
        ),
        migrations.AddIndex(
            model_name='integrationlocation',
            index=models.Index(fields=['location'], name='integration_locatio_b6b147_idx'),
        ),
        migrations.AddIndex(
            model_name='featurelocation',
            index=models.Index(fields=['landmark', 'feature_start', 'feature_end'], name='feature_loc_landmar_b0dc1b_idx'),
        ),
        migrations.AddIndex(
            model_name='featurelocation',
            index=models.Index(fields=['landmark', 'feature_start'], name='feature_loc_landmar_854860_idx'),
        ),
        migrations.AddIndex(
            model_name='featurelocation',
            index=models.Index(fields=['landmark', 'feature_end'], name='feature_loc_landmar_ac6aa2_idx'),
        ),
        migrations.AddIndex(
            model_name='featurelocation',
            index=models.Index(fields=['landmark'], name='feature_loc_landmar_b0db14_idx'),
        ),
        migrations.AddIndex(
            model_name='featurelocation',
            index=models.Index(fields=['feature_start', 'feature_end'], name='feature_loc_feature_9b352e_idx'),
        ),
        migrations.AddIndex(
            model_name='featurelocation',
            index=models.Index(fields=['feature_start'], name='feature_loc_feature_af2e5e_idx'),
        ),
        migrations.AddIndex(
            model_name='featurelocation',
            index=models.Index(fields=['feature_end'], name='feature_loc_feature_cf42cf_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='featurelocation',
            unique_together={('feature', 'landmark', 'feature_start', 'feature_end')},
        ),
        migrations.AddIndex(
            model_name='feature',
            index=models.Index(fields=['genome_version', 'feature_name'], name='features_genome__4410ce_idx'),
        ),
        migrations.AddIndex(
            model_name='feature',
            index=models.Index(fields=['feature_name'], name='features_feature_7735e6_idx'),
        ),
        migrations.AddIndex(
            model_name='feature',
            index=models.Index(fields=['genome_version'], name='features_genome__b7a95e_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='feature',
            unique_together={('genome_version', 'feature_name')},
        ),
    ]
