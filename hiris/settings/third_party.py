import os
from .base import env
# from hiris.apps.core.models import GenomeHost

# For UW_SAML
from django.urls import reverse_lazy


# print(f"Mock Username: {env('MOCK_USERNAME')}")

# For UW_SAML
LOGIN_URL = reverse_lazy('saml_login')

UW_SAML = {
    'strict': False,
    'debug': True,
    'sp': {
        'entityId': 'https://example.uw.edu/saml2',
        'assertionConsumerService': {
            'url': 'https://example.uw.edu/saml/sso',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
        },
        'singleLogoutService': {
            'url': 'https://example.uw.edu/saml/logout',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'NameIDFormat': 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified',
        'x509cert': '',
        # for encrypted saml assertions uncomment and add the private key
        # 'privateKey': '',
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
        'x509cert': '',
    },
    'security': {
        # for encrypted saml assertions
        # 'wantAssertionsEncrypted': True,
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


IMPORT_WIZARD = {
    'Importers': {
        'Genome': {
            'name': 'Genome',
            'description': 'Import an entire genome',
            'app': 'hiris.apps.core',
            'models': ['test'],
        },
        'Integrations':{
            'name': 'Integrations',
            'long_name': 'A list of integrations into a genome',
            # 'description': 'A test description of an Integration.',
        },
    }
}