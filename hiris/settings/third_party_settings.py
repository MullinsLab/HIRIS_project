import os
from .base_settings import env

# For UW_SAML

#if env('UW_SAML_CERT_DIR'):
if 'UW_SAML_CERT_DIR' in env:
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
            'entityId': 'https://hiris.washington.edu',
            'assertionConsumerService': {
                'url': 'https://hiris.washington.edu/saml/sso',
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
            },
            'singleLogoutService': {
                'url': 'https://hiris.washington.edu/saml/logout',
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


# SAML mocking
if env('SAML_MOCK', default=False):

    MOCK_SAML_ATTRIBUTES = {
        'uwnetid': [env('MOCK_USERNAME')],
        'affiliations': ['student', 'member'],
        'eppn': [env('MOCK_EMAIL')],
        'email': [env('MOCK_EMAIL')],
        'scopedAffiliations': ['student@washington.edu', 'member@washington.edu'],
        'isMemberOf': ['u_test_group', 'u_test_another_group'],
    }

    DJANGO_LOGIN_MOCK_SAML = {
        'NAME_ID': 'mock-nameid',
        'SESSION_INDEX': 'mock-session',
        'SAML_USERS': [
            {
                "username":env('MOCK_USERNAME'),
                "password": env('MOCK_PASSWORD'),
                "email": env('MOCK_EMAIL'),
                "MOCK_ATTRIBUTES" : {
                    'uwnetid': [env('MOCK_USERNAME')],
                    'affiliations': ['student', 'member'],
                    'eppn': [env('MOCK_EMAIL')],
                    'email': [env('MOCK_EMAIL')],
                    'scopedAffiliations': ['student@washington.edu', 'member@washington.edu'],
                    'isMemberOf': [
                        'u_test_group', 'u_test_another_group'
                    ],
                }
            }
        ]
    }