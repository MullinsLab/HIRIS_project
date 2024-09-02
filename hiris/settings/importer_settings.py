import os
from .base_settings import env
# from hiris.apps.core.utils.resolve_importer import accession_id_to_chromosome

ML_IMPORT_WIZARD = {
    "Working_Files_Dir": os.path.join("/", env("WORKING_FILES_DIR"), ""),
    "Logger": "app",
    "Log_Exceptions": True,
    "Setup_On_Start": True,
    "Max_Importer_Processes": 2,
    "Call_After_Import": "hiris.apps.core.utils.backend.process_after_import",
    'Importers': {
        "LandmarkChromosomes": {
            "name": "Landmark Chromosomes",
            "description": "Translation from accession ID to chromosome",
            "apps": [
                {
                    "name": "core",
                    "include_models": ["GenomeVersion", "LandmarkChromosome"],
                    "models": {
                        "GenomeVersion": {
                            "exclude_fields": ['external_gene_id_source'],
                            "load_value_fields": ["genome_version_name"],
                        },
                    },
                },
            ],
        },
        'Genome': {
            'name': 'Genome',
            'description': 'Import an entire genome',
            'apps': [
                {
                    'name': 'core',
                    'include_models': ['GenomeSpecies', "GenomeVersion", "GeneType", "FeatureType", "Feature", "FeatureLocation"],
                    # 'exclude_models': ['Feature'],
                    'models': {
                        'GenomeSpecies': {
                            'restriction': 'deferred',
                            "load_value_fields": ["genome_species_name"],
                        },
                        "GenomeVersion": {
                            "exclude_fields": ['external_gene_id_source'],
                            "default_option": "raw_text",
                            "load_value_fields": ["genome_version_name"],
                        },
                        'FeatureType': {
                            'restriction': 'rejected',
                            'fields': {
                                'feature_type_name': {
                                    'approved_values': ['CDS', 'exon', 'region', 'gene', 'start_codon', 'stop_codon']
                                },
                            },
                        },
                        "Feature": {
                            # "exclude_fields": ["external_gene_id"],
                        },
                        'FeatureLocation': {
                            "fields": {
                                "feature_orientation": {
                                    "critical": True,
                                    "translate_values": {"+": "F", "-": "R"},
                                    "force_case": "upper",  
                                },
                            },
                        },
                    },
                },
            ],
        },
        'Integrations':{
            'name': 'Integration Sites',
            'long_name': 'A list of integration sites in a genome',
            'description': 'A test description of an Integration.',
            'apps': [
                {
                    'name': 'core',
                    'include_models': ["GenomeVersion", "DataSet", "Publication", "DataSetSource", "Subject", "SubjectData", "Sample", "SampleData", "Preparation", "SequencingMethod", "IntegrationEnvironment", "Integration", "IntegrationLocation", "BlastInfo"],
                    "models": {
                        "GenomeVersion": {
                            "exclude_fields": ["external_gene_id_source"],
                            "restriction": "rejected",
                            "load_value_fields": ["genome_version_name"],
                        },
                        "DataSet": {
                            "exclude_fields": ["users", "groups"],
                        },
                        "Integration": {
                            "critical": True,
                            "minimum_objects": False,
                        },
                        "IntegrationEnvironment": {
                            "load_value_fields": ["integration_environment_name"],
                        },
                        "IntegrationLocation": {
                            "critical": True,
                            "minimum_objects": False,
                            "fields": {
                                "orientation_in_landmark": {
                                    "critical": True,
                                    "translate_values": {"+": "F", "-": "R"},
                                    "force_case": "upper",  
                                },
                                "landmark": {
                                    "resolvers": ["hiris.apps.core.utils.resolve_importer.translate_chromosome_to_accession_id"],
                                }, 
                            },
                        },
                        "BlastInfo": {
                            "suppress_on_empty": True,
                        },
                        "DataSetSource": {
                            "exclude_fields": ["document_citation_url", "document_citation_doi", "document_citation_issn", "document_citation_year", "document_citation_type", "document_citation_pages", "document_citation_title", "document_citation_author", "document_citation_issue_number", "document_citation_volume", "document_citation_journal", "document_citation_citekey"]
                        },
                        "SubjectData": {
                            "key_value_model": True,
                            "restriction": "deferred",
                            # "key_field": "key",
                            # "value_field": "value",
                            "restrict_on_key": True,
                            "restrict_on_value": False,
                            "initial_values": [], # List of initial keys to show in the keys dropdown
                            "minimum_objects": True, # Defaults to True.  Treats all fields (including child key/value models) as unique so it doesn't create duplicate objects
                        },
                        "Sample": {
                            "exclude_fields": ["culture", "culture_day", "date", "disease", "genbank", "original_id", "provirus_activity", "replicates", "tissue", "tissue_url", "type", "visit", "years_on_art"]
                        },
                        "SampleData": {
                            "key_value_model": True,
                            "restriction": "deferred",
                            "restrict_on_key": True,
                            "restrict_on_value": False,
                            "initial_values": [],
                        },
                    },
                },
            ],
        },
    }
}