import os
from .base_settings import env

ML_EXPORT_WIZARD = {
    'Working_Files_Dir': os.path.join('/', env('WORKING_FILES_DIR'), ''),
    'Logger': 'app',
    "Setup_On_Start": True,
    'Exporters': [
        {
            "name": "IntegrationFeatures",
            "exclude_fields": ["added", "updated"],
            "apps" : [
                {
                    "name": "core",
                    #"include_models": [],
                    #"exclude_models": [],
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
            "name": "IntegrationFeaturesSummary",
            "rollups": [
                {
                    "name": "IntegrationFeaturesSummary",
                    "exporter": "IntegrationFeatures",
                    "group_by": ["integration_environment_name", "subject_identifier", "core.IntegrationFeature.feature_type_name", "core.IntegrationLocation.landmark", "location", "orientation_in_landmark", "feature_orientation", "gene_type_name", "feature_name", "feature_id"],
                    "extra_field": [{"column_name": "multiplicity", "function": "count"}],
                },
            ],
        },
        {
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