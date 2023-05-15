import os
from .base import env
# from hiris.apps.core.models import GenomeSpecies

# # For UW_SAML
# from django.urls import reverse_lazy
# #LOGIN_URL = reverse_lazy('saml_login')
# LOGIN_URL = reverse_lazy('login')
# LOGIN_REDIRECT_URL = "/"

if env('UW_SAML_CERT_DIR'):
    UW_SAML_CERT_DIR = env('UW_SAML_CERT_DIR')

    UW_SAML_PRIVATE_KEY = env('UW_SAML_PRIVATE_KEY')
    with open(os.path.join(UW_SAML_CERT_DIR, UW_SAML_PRIVATE_KEY), "r") as file:
        UW_SAML_PRIVATE_KEY = file.read()

    UW_SAML_PUBLIC_CERT = env('UW_SAML_PUBLIC_CERT')
    with open(os.path.join(UW_SAML_CERT_DIR, UW_SAML_PUBLIC_CERT), "r") as file:
        UW_SAML_PUBLIC_CERT = file.read()

    UW_SAML_IDPCERT = env('UW_SAML_IDPCERT')
    with open(os.path.join(UW_SAML_CERT_DIR, UW_SAML_IDPCERT), "r") as file:
        UW_SAML_IDPCERT = file.read()

UW_SAML = {
    'strict': False,
    'debug': True,
    'sp': {
        'entityId': 'https://dev.hiris.washington.edu',
        'assertionConsumerService': {
            'url': 'https://dev.hiris.washington.edu/saml/sso',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
        },
        'singleLogoutService': {
            'url': 'https://dev.hiris.washington.edu/saml/logout',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'NameIDFormat': 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified',
        'x509cert': UW_SAML_PUBLIC_CERT,
        # for encrypted saml assertions uncomment and add the private key
        'privateKey': UW_SAML_PRIVATE_KEY,
    },
    'idp': {
        'entityId': 'urn:mace:incommon:washington.edu',
        'singleSignOnService': {
            'url': 'https://idp.u.washington.edu/idp/profile/SAML2/Redirect/SSO',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'singleLogoutService': {
            'url': 'https://idp.u.washington.edu/idp/logout',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'x509cert': UW_SAML_IDPCERT,
    },
    'security': {
        # for encrypted saml assertions
        'wantAssertionsEncrypted': True,
        # for 2FA uncomment this line
        # 'requestedAuthnContext':  ['urn:oasis:names:tc:SAML:2.0:ac:classes:TimeSyncToken']
    }
}

# Mock login for testing
# DJANGO_LOGIN_MOCK_SAML = {
#     'NAME_ID': 'mock-nameid',
#     'SESSION_INDEX': 'mock-session',
#     'SAML_USERS': [
#         {
#             "username": env('MOCK_USERNAME'),
#             "password": 'saml',
#             "email": 'saml@darleyconsulting.com',
#             "MOCK_ATTRIBUTES" : {
#                 'uwnetid': ['saml@uw.edu'],
#                 'affiliations': ['student', 'member'],
#                 'eppn': ['javerage@washington.edu'],
#                 'scopedAffiliations': ['student@washington.edu', 'member@washington.edu'],
#                 'isMemberOf': [
#                     'u_test_group', 'u_test_another_group'
#                 ],
#             }
#         }
#     ]
# }


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
                    'include_models': ['GenomeVersion', 'DataSet', "DataSetSource", "Subject", "Sample", "Preparation", "SequencingMethod", "IntegrationEnvironment", "Integration", "IntegrationLocation", "BlastInfo"],
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
                    },
                },
            ],
        },
    }
}