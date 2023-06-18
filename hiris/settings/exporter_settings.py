import os
from .base_settings import env

ML_EXPORT_WIZARD = {
    'Working_Files_Dir': os.path.join('/', env('WORKING_FILES_DIR'), ''),
    'Logger': 'app',
    "Setup_On_Start": True,
    'Exporters': [
        {
            # IntegrationFeatures
            "name": "IntegrationFeatures",
            "exclude_fields": ["added", "updated"],
            "apps" : [
                {
                    "name": "core",
                    #"include_models": [],
                    "exclude_models": ["PublicationData", "SubjectData", "SampleData"],
                    "primary_model": "IntegrationLocation",
                    "models": {
                        "Integration": {
                            "dont_link_to": ["DataSet"]
                        },
                        "DataSet": {
                            "dont_link_to": ["GenomeVersion"]
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
                    "group_by": ["integration_environment_name", "subject_identifier", "core.IntegrationFeature.feature_type_name", "core.IntegrationLocation.landmark", "location", "orientation_in_landmark", "feature_orientation", "gene_type_name", "feature_name"], #, "feature_id"
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
                            "when": {
                                "condition": "in vivo",
                                "extra_field": {
                                    "function": "count",
                                    "source_field": "subject_identifier",
                                    "distinct": True,
                                },
                            }
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
                    "group_by": ["integration_environment_name", "feature_name", "gene_type_name"],
                },
            ],
        },
        {
            #Integrations
            "name": "Integrations",
            "apps" : [
                {
                    "name": "core",
                    "include_models": ["IntegrationLocation", "Integration", "BlastInfo", "IntegrationEnvironment", "SequencingMethod", "Preparation", "Sample", "Subject", "DataSet", "Publication", "DataSetSource", "GenomeVersion", "GenomeSpecies"],
                    "primary_model": "IntegrationLocation",
                    "models": {
                        "Integration": {
                            "dont_link_to": ["DataSet"]
                        },
                        "DataSet": {
                            "dont_link_to": ["GenomeVersion"]
                        },
                    },
                },
            ],
        },
    ]
}