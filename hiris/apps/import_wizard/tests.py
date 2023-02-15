import json
from django.test import TestCase
from .tools import dict_hash


class InclusionTest(TestCase):
    ''' A test to make sure the Import Wizard app is being included '''
    def test_true_is_true(self):
        ''' Makesure True is True '''
        self.assertTrue(True)


class TemplateAndViewTests(TestCase):
    ''' Test the templates/views in Import Wizard '''
    def test_root_should_have_genome_and_integrations_items(self):
        ''' Make sure we're getting a success status code and hitting the correct template, as well as including the Imports from settings '''
        response = self.client.get("/import/")
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'import_manager.django-html')
        self.assertContains(response, 'Genome')
        self.assertContains(response, 'integrations')


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