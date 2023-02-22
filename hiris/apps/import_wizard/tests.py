import logging
log = logging.getLogger('test')

import json

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from .models import ImportScheme, ImportFile
from .tools import dict_hash


class InclusionTest(TestCase):
    ''' A test to make sure the Import Wizard app is being included '''

    def test_true_is_true(self):
        ''' Makesure True is True '''
        self.assertTrue(True)


class TemplateAndViewTests(TestCase):
    ''' Test the templates/views in Import Wizard '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up whatever objects are going to be needed for all tests '''

        cls.user = User.objects.create(username='testuser')
        cls.user.set_password('12345')
        cls.user.save()

    
    def setUp(self):
        ''' Log in the user '''
        
        self.client.login(username=self.user.username, password='12345')


    def test_root_should_have_genome_and_integrations_items(self):
        ''' Make sure we're getting a success status code and hitting the correct template, as well as including the Imports from settings '''

        response = self.client.get("/import/")
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'import_manager.django-html')
        self.assertContains(response, 'Genome')
        self.assertContains(response, 'integrations')


class ModelTests(TestCase):
    '''  Tests of basic model functionality '''

    def test_import_scheme_has_gets_created_correctly(self):
        ''' A new ImportScheme model should have a hash '''

        my_import_scheme = ImportScheme(
            name = 'Test Importer', 
            user = User.objects.first(), 
            importer = 'Genome',
            status = 0,
        )
        my_import_scheme.save()
        log.debug(f'ImporteScheme: Importer {my_import_scheme.importer} has hash {my_import_scheme.importer_hash}.')

        my_import_file = ImportFile(name='test.txt', import_scheme=my_import_scheme)
        my_import_file.save()

        self.assertEquals(32, len(my_import_scheme.importer_hash))
        self.assertEquals(dict_hash(settings.IMPORT_WIZARD['Importers']['Genome']), my_import_scheme.importer_hash)
        self.assertEquals('00000001', my_import_file.file_name)


class ThirdPartyTest(TestCase):
    ''' Tests for third party '''

    def test_dict_hash_returns_correct_hash(self):
        ''' Ensure that the hash for our dictionary is consistant and correct, as well as different from other hashes '''

        dict1 = {'test': {'count': 1, 'number': 89.3, 'name': 'my test'}}
        dict2 = {'test': {'count': 1, 'name': 'my test', 'number': 89.3}}
        dict3 = {'test': {'count': 1, 'number': 89.3, 'name': 'my test 3'}}

        self.assertEqual('c7a98aa3381012984c03edeaf7049096', dict_hash(dict1))
        self.assertEqual(dict_hash(dict1), dict_hash(dict2))
        self.assertEqual(dict_hash(dict1), dict_hash(dict1))
        self.assertNotEqual(dict_hash(dict1), dict_hash(dict3))