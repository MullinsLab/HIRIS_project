import os
from .base_settings import env

ML_IMPORT_WIZARD = {
    'Working_Files_Dir': os.path.join('/', env('WORKING_FILES_DIR'), ''),
    'Logger': 'app',
    "Setup_On_Start": True,
    'Importers': {
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
                            "exclude_fields": ["external_gene_id"],
                        },
                        'FeatureLocation': {
                            "critical": True,
                            "translate_values": {"+": "F", "-": "R"},
                            "force_case": "upper",
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
                    'include_models': ["GenomeVersion", "DataSet", "Publication", "DataSetSource", "Subject", "SubjectData", "Sample", "Preparation", "SequencingMethod", "IntegrationEnvironment", "Integration", "IntegrationLocation", "BlastInfo"],
                    "models": {
                        "GenomeVersion": {
                            "exclude_fields": ["external_gene_id_source"],
                            "restriction": "rejected",
                            "load_value_fields": ["genome_version_name"],
                        },
                        "Integration": {
                            "critical": True,
                        },
                        "IntegrationLocation": {
                            "critical": True,
                        },
                        "BlastInfo": {
                            "suppress_on_empty": True,
                        },
                        "DataSetSource": {
                            "exclude_fields": ["document_citation_url", "document_citation_doi", "document_citation_issn", "document_citation_year", "document_citation_type", "document_citation_pages", "document_citation_title", "document_citation_author", "document_citation_issue_number", "document_citation_volume", "document_citation_journal", "document_citation_citekey"]
                        },
                        "SubjectData": {
                            "column_to_row": True,
                            "restriction": "deferred",
                            "restrict_on_column": "key"
                        }
                    },
                },
            ],
        },
    }
}