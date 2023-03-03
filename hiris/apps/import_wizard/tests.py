import logging
log = logging.getLogger('test')

import json
from http import HTTPStatus

from django.test import TestCase, TransactionTestCase, SimpleTestCase
from django.contrib.auth.models import User
from django.conf import settings

from .models import ImportScheme, ImportFile
from .tools import dict_hash, sound_user_name


class InclusionTest(TestCase):
    ''' A test to make sure the Import Wizard app is being included '''

    def test_true_is_true(self):
        ''' Makesure True is True '''
        self.assertTrue(True)
        

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
        
    def test_import_scheme_hash_should_be_the_correct_length(self):
        self.assertEquals(32, len(self.import_scheme.importer_hash))

    def test_import_scheme_hash_should_be_the_same_as_the_hash_of_the_raw_dict_from_settings(self):
        self.assertEquals(dict_hash(settings.IMPORT_WIZARD['Importers']['Genome']), self.import_scheme.importer_hash)

    def test_import_file_name_should_be_file_id_padded_to_8_digits(self):
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

    def test_import_scheme_class_returns_correct_status_value_by_label(self):
        ''' ImportSchemeFile class should return the correct status when given a certain value '''

        self.assertEqual(0, ImportScheme.status_from_label('New'))
        self.assertEqual(0, ImportScheme.status_from_label('neW'))
        self.assertEqual(1, ImportScheme.status_from_label('File Received'))

    def test_import_scheme_file_class_returns_correct_status_value_by_lable(self):
        ''' ImportSchemeFile class should return the correct status when given a certain value '''

        self.assertEquals(0, ImportFile.status_from_label('New'))
        self.assertEquals(5, ImportFile.status_from_label('Imported'))
        self.assertEquals(5, ImportFile.status_from_label('importeD'))


# Tests for Tools
class DictHashTest(TestCase):
    ''' Tests for DictHash '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up dome dicts to test with '''
        cls.dict1 = {'test': {'count': 1, 'number': 89.3, 'name': 'my test'}}
        cls.dict2 = {'test': {'count': 1, 'name': 'my test', 'number': 89.3}}
        cls.dict3 = {'test': {'count': 1, 'number': 89.3, 'name': 'my test 3'}}

    def test_dict_hash_returns_correct_hash(self):
        self.assertEqual('c7a98aa3381012984c03edeaf7049096', dict_hash(self.dict1))

    def test_dict_hash_returns_same_hash_with_different_order(self):
        self.assertEqual(dict_hash(self.dict1), dict_hash(self.dict2))

    def test_dict_hash_returns_same_hash_with_the_same_dict(self):
        self.assertEqual(dict_hash(self.dict1), dict_hash(self.dict1))
    
    def test_dict_hash_returns_different_hash_with_the_different_dict(self):
        self.assertNotEqual(dict_hash(self.dict1), dict_hash(self.dict3))


class SoundUserNameTests(TestCase):
    ''' Tests for sound_user_name, a function that returns a good name for a user '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up some users to test with '''

        cls.user1 = User(username='username')
        cls.user2 = User(username='username', first_name='first_name')
        cls.user3 = User(username='username', last_name='last_name')
        cls.user4 = User(username='username', first_name='first_name', last_name='last_name')

    def test_sound_user_name_with_only_username_returns_username(self):
        self.assertEqual(sound_user_name(self.user1), 'username')
    
    def test_sound_user_name_with_username_and_first_name_returns_first_name(self):
        self.assertEqual(sound_user_name(self.user2), 'first_name')
    
    def test_sound_user_name_with_username_and_last_name_returns_last_name(self):
        self.assertEqual(sound_user_name(self.user3), 'last_name')

    def test_sound_user_name_with_all_names_returns_first_name_last_name(self):
        self.assertEqual(sound_user_name(self.user4), 'first_name last_name')

    
class TemplateAndViewTests(SimpleTestCase):
    ''' Test the templates/views in Import Wizard '''

    databases = '__all__'

    @classmethod
    def setUpTestData(cls):
        ''' Set up whatever objects are going to be needed for all tests '''

        cls.user = User.objects.create(username='testuser')
        cls.user.set_password('12345')
        cls.user.save()

        # cls.import_scheme = ImportScheme(
        #     name = 'Test Importer', 
        #     user = cls.user, 
        #     importer = 'Genome',
        #     status = 0,
        # )
        # cls.import_scheme.save()
    
    def setUp(self):
        ''' Log in the user '''

        if User.objects.first():
            self.user = User.objects.first()
        else:
            self.user = User.objects.create(username='testuser')
            self.user.set_password('12345')
            self.user.save()

        self.client.login(username=self.user.username, password='12345')


    def test_root_should_have_genome_and_integrations_items_and_template_is_manager(self):
        ''' Make sure we're getting a success status code and hitting the correct template, as well as including the Imports from settings '''

        response = self.client.get("/import/")
        
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'import_wizard/manager.django-html')
        self.assertContains(response, 'Genome')
        self.assertContains(response, 'integration')

    def test_genome_should_have_form_name_and_template_is_new_scheme(self):
        ''' Make sure we're getting a success status code and hitting the correct template, as well as getting a form. '''

        response = self.client.get("/import/Genome")
        
        log.debug(response)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'import_wizard/new_scheme.django-html')
        self.assertContains(response, '<form class="form-horizontal"')

    def test_genome_post_should_result_in_new_ImportScheme_object_have_template_manager(self):
        ''' Use /import/Genome to add a genome import, test the return status, '''
        response = self.client.post("/import/Genome", data={'name': 'Test Importer from Page', 'description': 'testing'})

        import_scheme = ImportScheme.objects.filter(user_id=self.user.id).first()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(import_scheme.name, 'Test Importer from Page')

    # def test_genome_get_should_list_test_importer(self):
    #     ''' /import/Genome should have the importer we created in the previous test '''
        response = self.client.get("/import/")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'import_wizard/manager.django-html')
        self.assertContains(response, 'Test Importer from Page')