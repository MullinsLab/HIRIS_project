import logging
log = logging.getLogger('test')

import json

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from .models import ImportScheme, ImportFile
from .tools import dict_hash, sound_user_name


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
        self.assertTemplateUsed(response, 'import_wizard/manager.django-html')
        self.assertContains(response, 'Genome')
        self.assertContains(response, 'integration')


class ModelTests(TestCase):
    '''  Tests of basic model functionality '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up whatever objects are going to be needed for all tests '''    

        cls.import_scheme = ImportScheme(
            name = 'Test Importer', 
            user = User.objects.first(), 
            importer = 'Genome',
            status = 0,
        )
        cls.import_scheme.save()

        cls.import_file_1 = ImportFile(name='test1.txt', import_scheme=cls.import_scheme)
        cls.import_file_1.save()
        
    
    def test_import_scheme_has_gets_created_correctly(self):
        ''' A new ImportScheme model should have a hash '''

        log.debug(f'ImporteScheme: Importer {self.import_scheme.importer} has hash {self.import_scheme.importer_hash}.')

        self.assertEquals(32, len(self.import_scheme.importer_hash))
        self.assertEquals(dict_hash(settings.IMPORT_WIZARD['Importers']['Genome']), self.import_scheme.importer_hash)
        self.assertEquals('00000001', self.import_file_1.file_name)
    

    def test_import_scheme_can_list_its_files(self):
        ''' Test that ImportScheme.list_files() works correctly '''
        
        log.debug(f'File list for {self.import_scheme} is {self.import_scheme.list_files()}')

        self.assertEquals('test1.txt', self.import_scheme.list_files())

        import_file_2 = ImportFile(name='test2.txt', import_scheme=self.import_scheme)
        import_file_2.save()

        self.assertEquals('test1.txt, test2.txt', self.import_scheme.list_files())
        self.assertEquals('test1.txt<br>test2.txt', self.import_scheme.list_files(separator='<br>'))

    def test_import_scheme_file_has_correct_file_type(self):
        ''' ImportSchemeFile should have the correct type '''
        
        self.assertEquals('txt', self.import_file_1.type)

class ToolsTest(TestCase):
    ''' Tests for tools '''

    def test_dict_hash_returns_correct_hash(self):
        ''' Ensure that the hash for our dictionary is consistant and correct, as well as different from other hashes '''

        dict1 = {'test': {'count': 1, 'number': 89.3, 'name': 'my test'}}
        dict2 = {'test': {'count': 1, 'name': 'my test', 'number': 89.3}}
        dict3 = {'test': {'count': 1, 'number': 89.3, 'name': 'my test 3'}}

        self.assertEqual('c7a98aa3381012984c03edeaf7049096', dict_hash(dict1))
        self.assertEqual(dict_hash(dict1), dict_hash(dict2))
        self.assertEqual(dict_hash(dict1), dict_hash(dict1))
        self.assertNotEqual(dict_hash(dict1), dict_hash(dict3))


    def test_sound_user_name_returns_correct_value(self):
        '''  Ensure that the return value for sound_user_name is correct'''

        user1 = User(username='username')
        user2 = User(username='username', first_name='first_name')
        user3 = User(username='username', last_name='last_name')
        user4 = User(username='username', first_name='first_name', last_name='last_name')

        self.assertEqual(sound_user_name(user1), 'username')
        self.assertEqual(sound_user_name(user2), 'first_name')
        self.assertEqual(sound_user_name(user3), 'last_name')
        self.assertEqual(sound_user_name(user4), 'first_name last_name')