import logging
log = logging.getLogger('test')

import json
from http import HTTPStatus

from django.test import TestCase, TransactionTestCase, SimpleTestCase
from django.contrib.auth.models import User
from django.conf import settings

from .models import ImportScheme, ImportSchemeFile
from .utils.simple import dict_hash, sound_user_name, split_by_caps, stringalize, mached_name_choices, fancy_name


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

        cls.import_file_1 = ImportSchemeFile(name='test1.txt', import_scheme=cls.import_scheme)
        cls.import_file_1.save()
        
    def test_import_scheme_hash_should_be_the_correct_length(self):
        self.assertEquals(32, len(self.import_scheme.importer_hash))

    def test_import_scheme_hash_should_be_the_same_as_the_hash_of_the_raw_dict_from_settings(self):
        self.assertEquals(dict_hash(settings.ML_IMPORT_WIZARD['Importers']['Genome']), self.import_scheme.importer_hash)

    def test_import_file_name_should_be_file_id_padded_to_8_digits(self):
        self.assertEquals('00000001', self.import_file_1.file_name)
    

    def test_import_scheme_can_list_its_files(self):
        ''' Test that ImportScheme.list_files() works correctly '''
        
        log.debug(f'File list for {self.import_scheme} is {self.import_scheme.list_files()}')

        self.assertEquals('test1.txt', self.import_scheme.list_files())

        import_file_2 = ImportSchemeFile(name='test2.txt', import_scheme=self.import_scheme)
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

        self.assertEquals(0, ImportSchemeFile.status_from_label('New'))
        self.assertEquals(5, ImportSchemeFile.status_from_label('Imported'))
        self.assertEquals(5, ImportSchemeFile.status_from_label('importeD'))


# Tests for simple utils
class SimpleUtilsTest(TestCase):
    ''' Tests for functions from the utils.simple module '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up dome dicts to test with '''
        cls.dict1 = {'test': {'count': 1, 'number': 89.3, 'name': 'my test'}}
        cls.dict2 = {'test': {'count': 1, 'name': 'my test', 'number': 89.3}}
        cls.dict3 = {'test': {'count': 1, 'number': 89.3, 'name': 'my test 3'}}

    # dict_hash() tests
    def test_dict_hash_returns_correct_hash(self):
        """ dict_hash() should return c7a98aa3381012984c03edeaf7049096 when the input is self.dict1 """
        self.assertEqual('c7a98aa3381012984c03edeaf7049096', dict_hash(self.dict1))

    def test_dict_hash_returns_same_hash_with_different_order(self):
        """ dict_hash() should return the same hash when the input is the same except for the order of the elements """
        self.assertEqual(dict_hash(self.dict1), dict_hash(self.dict2))

    def test_dict_hash_returns_same_hash_with_the_same_dict(self):
        """ dict_hash() should return the same hash when the input is the same """
        self.assertEqual(dict_hash(self.dict1), dict_hash(self.dict1))
    
    def test_dict_hash_returns_different_hash_with_the_different_dict(self):
        """ dict_hash() should return different hashes when the input is different """
        self.assertNotEqual(dict_hash(self.dict1), dict_hash(self.dict3))
    
    # Stringalization tests
    def test_stringalize_returns_a_string_when_given_an_int(self):
        """ stringalize() should return a string when given an int """
        self.assertEqual("1", stringalize(1))

    def test_stringalize_returns_a_string_when_given_a_string(self):
        """ stringalize() should return a string when given a string """
        self.assertEqual("string", stringalize("string"))

    def test_stringalize_returns_a_string_when_given_a_set(self):
        """ stringalize() should return a string when given a set """
        self.assertEqual("1, 2", stringalize({1, "2"}))

    def test_stringalize_returns_a_string_when_given_a_list(self):
        """ stringalize() should return a string when given a list """
        self.assertEqual("1, 2", stringalize(["1", 3-1]))

    def test_stringalize_returns_a_string_when_given_a_tuple(self):
        """ stringalize() should return a string when given a tuple """
        self.assertEqual("1, 2", stringalize((1, '2')))

    # List manipulation tests
    def test_mached_name_choices_should_return_doubled_list_of_tuples(self):
        """ mached_name_choices() should return a list that is composed of the members of the input list duplicated as a tuple """
        self.assertEqual([(1, 1), ("test", "test")], mached_name_choices([1, "test"]))

    # string formatting tests
    def test_split_by_caps_returns_list_of_words_split_by_capital_letters(self):
        """ split_by_caps() should return a list of words split by capital letters """
        self.assertEqual(split_by_caps('MyTest'), ['My', 'Test'])
    
    def test_split_by_caps_returns_a_one_item_list_when_given_a_string_with_no_caps(self):
        """ split_by_caps() should return a list of one word when given a string with no capital letters """
        self.assertEqual(split_by_caps("mytest"), ["mytest"])

    def test_fancy_name_returns_string_initial_caps_when_given_a_string(self):
        """ fancy_name() should return a string with initial caps when given a string """
        self.assertEqual("My Test!", fancy_name("my test!"))

    def test_fancy_name_returns_string_initial_caps_when_given_a_string(self):
        """ fancy_name() should return a string with initial caps when given a string """
        self.assertEqual("My Test", fancy_name("my test"))

    def test_fancy_name_returns_string_initial_caps_when_given_a_underscored_string(self):
        """ fancy_name() should return a string with initial caps when given an underscored string """
        self.assertEqual("My Test", fancy_name("my_test"))

    def test_fancy_name_returns_string_initial_caps_when_given_a_camelcased_string(self):
        """ fancy_name() should return a string with initial caps when given a CamelCased string """
        self.assertEqual("My Test", fancy_name("myTest"))

    def test_fancy_name_returns_string_with_capital_id(self):
        """ fancy_name should return the word ID as caps, instead of title case (Id) """
        self.assertEqual("My ID Test", fancy_name("my_id test"))

    def test_fancy_name_returns_string_with_capital_id_at_the_beginning_of_a_string(self):
        """ fancy_name should return the word ID as caps, instead of title case (Id) at the beginning of a string """
        self.assertEqual("ID My ID Test", fancy_name("Id my_id test"))

    def test_fancy_name_returns_string_with_capital_id_at_the_end_of_a_string(self):
        """ fancy_name should return the word ID as caps, instead of title case (Id) at the end of a string """
        self.assertEqual("My ID Test ID", fancy_name("my_id test_id"))

    def test_fancy_name_returns_capital_id_if_string_is_id(self):
        """ fancy_name() should return ID if the string is just id """
        self.assertEqual("ID", fancy_name("id"))


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
        self.assertTemplateUsed(response, 'ml_import_wizard/manager.django-html')
        self.assertContains(response, 'Genome')
        self.assertContains(response, 'integration')

    def test_genome_should_have_form_name_and_template_is_new_scheme(self):
        ''' Make sure we're getting a success status code and hitting the correct template, as well as getting a form. '''

        response = self.client.get("/import/Genome")
        
        log.debug(response)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'ml_import_wizard/new_scheme.django-html')
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
        self.assertTemplateUsed(response, 'ml_import_wizard/manager.django-html')
        self.assertContains(response, 'Test Importer from Page')