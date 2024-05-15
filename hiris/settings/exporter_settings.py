import os
from .base_settings import env

ML_EXPORT_WIZARD = {
    'Working_Files_Dir': os.path.join('/', env('WORKING_FILES_DIR'), ''),
    'Logger': 'app',
    'Log_Exceptions': True,
    "Setup_On_Start": True,
    'Exporters': [
        {
            # IntegrationFeatures - Broad export that contains all the features for all the integrations
            "name": "IntegrationFeatures",
            "exclude_fields": ["added", "updated"],
            "extra_field":[
                {
                    "column_name": "orientation_in_feature",
                    "function": "case",
                    "case_expression": {
                        "source_field": ["orientation_in_landmark", "feature_orientation"],
                        "operator": "join",
                    },
                    "when": [
                        {"condition": "FF", "value": "F"},
                        {"condition": "RR", "value": "F"},
                        {"condition": "FR", "value": "R"},
                        {"condition": "RF", "value": "R"},
                    ],
                },
            ],
            "compound_filter": {
                "operator": "or",
                "filters": [
                    {
                        "field": "data_set_id",
                        "operator": "in",
                        "value": {"type": "query", "query": "(SELECT data_set_id FROM data_set_users WHERE user_id = {user_id})"},
                    },
                    {
                        "field": "data_set_id",
                        "operator": "in",
                        "query": "(SELECT dataset_id FROM data_sets_groups JOIN auth_user_groups using (group_id) WHERE user_id={user_id})",
                    },
                ],
            },
            "apps" : [
                {
                    "name": "core",
                    #"include_models": [],
                    "exclude_models": ["PublicationData", "SubjectData", "SampleData", "LandmarkChromosome"],
                    "primary_model": "IntegrationLocation",
                    "models": {
                        "Integration": {
                            "dont_link_to": ["DataSet"]
                        },
                        "DataSet": {
                            "dont_link_to": ["GenomeVersion"],
                        },
                    },
                }
            ],
        },
        {
            # IntegrationFeaturesSummary
            "name": "IntegrationFeaturesSummary",
            "rollups": [
                {
                    "name": "IntegrationFeaturesSummary",
                    "exporter": "IntegrationFeatures",
                    "group_by": ["integration_environment_name", "subject_identifier", "core.IntegrationFeature.feature_type_name", "core.IntegrationLocation.landmark", "location", "orientation_in_landmark", "feature_orientation", "orientation_in_feature", "gene_type_name", "feature_name", "external_gene_id"],
                    "extra_field": [{"column_name": "multiplicity", "function": "count"}],
                },
            ],
        },
        {
            # SummaryByGene
            "name": "SummaryByGene",
            "rollups": [
                {
                    "name": "SummaryByGene",
                    "exporter": "IntegrationFeaturesSummary",
                    "where_before_join": {
                        "IntegrationFeature": [
                            {
                                "field": "feature_type_name",
                                "value": "gene",
                            },
                        ],
                    },
                    "extra_field":[
                        {
                            "column_name": "subjects",
                            "function": "case",
                            "source_field": "integration_environment_name",
                            "when": [
                                {
                                    "condition": "in vivo",
                                    "extra_field": {
                                        "function": "count",
                                        "source_field": "subject_identifier",
                                        "distinct": True,
                                    },
                                }
                            ],
                        },
                        {
                            "column_name": "unique_sites",
                            "function": "count",
                            "source_field": ["landmark", "location"]
                        },
                        {
                            "column_name": "proliferating_sites",
                            "function": "count",
                            "source_field": ["landmark", "location"],
                            "filter": [
                                {
                                    "field": "multiplicity",
                                    "operator": ">=",
                                    "value": 2,
                                },
                            ]
                        },
                        {
                            "column_name": "total_in_gene",
                            "function": "sum",
                            "source_field": "multiplicity",
                            "cast": "int",
                        },
                    ],
                    "group_by": ["integration_environment_name", "feature_name", "gene_type_name", "external_gene_id"],
                },
            ],
        },
        {
            #IntegrationsGeneSummary
            "name": "IntegrationsGeneSummary",
            "rollups": [
                {
                    "name": "IntegrationsGeneSummary",
                    "exporter": "IntegrationFeatures",
                    "group_by": ["integration_environment_name", "subject_identifier", "core.IntegrationLocation.landmark", "location", "chromosome", "orientation_in_landmark", "gene_type_name", "feature_name", "external_gene_id", "feature_start"],
                    "where_before_join": {
                        "IntegrationFeature": [
                            {
                                "field": "feature_type_name",
                                "value": "gene",
                            },
                        ],
                    },
                    "extra_field": [
                        {
                            "column_name": "multiplicity", 
                            "function": "count",
                        },
                        {
                            "column_name": "source_names", 
                            "function": "aggragate", 
                            "source_field": "data_set_name", 
                            "order": "ASC", 
                            "distinct": True,
                            "field_type": "text",
                        },
                        {
                            "column_name": "pubmed_ids", 
                            "function": "aggragate", 
                            "source_field": "publication_pubmed_id", 
                            "order": "ASC", 
                            "distinct": True,
                            "field_type": "text",
                        },
                    ],
                },
            ],
        },
        {
            #Integrations
            "name": "Integrations",
            "apps": [
                {
                    "name": "core",
                    "include_models": ["IntegrationLocation", "Integration", "BlastInfo", "IntegrationEnvironment", "SequencingMethod", "Preparation", "Sample", "Subject", "DataSet", "Publication", "DataSetSource", "GenomeVersion", "GenomeSpecies"],
                    "primary_model": "IntegrationLocation",
                    "exclude_models": ["LandmarkChromosome"],
                    "models": {
                        "Integration": {
                            "dont_link_to": ["DataSet"]
                        },
                        # "DataSet": {
                        #     "dont_link_to": ["GenomeVersion"]
                        # },
                    },
                },
            ],
        },
        {
            #IntegrationsSummary
            "name": "IntegrationsSummary",
            "rollups": [
                {
                    "name": "IntegrationsSummary",
                    "exporter": "Integrations",
                    "group_by": ["integration_environment_name", "subject_identifier", "landmark", "location", "orientation_in_landmark", "genome_version_name"],
                    "extra_field": [
                        {
                            "column_name": "multiplicity", 
                            "function": "count",
                        },
                        {
                            "column_name": "source_names", 
                            "function": "aggragate", 
                            "source_field": "data_set_name", 
                            "order": "ASC", 
                            "distinct": True,
                            "field_type": "text",
                        },
                        {
                            "column_name": "pubmed_ids", 
                            "function": "aggragate", 
                            "source_field": "publication_pubmed_id", 
                            "order": "ASC", 
                            "distinct": True,
                            "field_type": "text",
                        },
                    ],
                },
            ],
        },
    ]
}