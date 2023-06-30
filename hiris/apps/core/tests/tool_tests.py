from django.test import TestCase
from django.urls import reverse  

from hiris.apps.core.models import GenomeVersion, GenomeSpecies, FeatureLocation, FeatureType, GeneType, Feature

class ModelTests(TestCase):
    ''' Tests that just test model structure and functions '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up all the test data for ModelTests '''
        cls.my_genome_species = GenomeSpecies.objects.create(genome_species_name='My Genome Species')
        cls.my_genome_version = GenomeVersion.objects.create(genome_version_name='My Genome', genome_species=cls.my_genome_species)
        cls.my_gene_type = GeneType.objects.create(gene_type_name='My Gene Type')
        cls.my_feature_type = FeatureType.objects.create(feature_type_name='Gene')
        cls.my_feature = Feature.objects.create(feature_name='My Gene', genome_version=cls.my_genome_version, feature_type=cls.my_feature_type, gene_type=cls.my_gene_type)
        cls.my_feature_location = FeatureLocation(feature=cls.my_feature, chromosome='chr1', landmark='NC_00002.2', feature_start=1231, feature_end=234234, feature_orientation='F')


    def test_core_base_class_should_return_names_that_match_objects_name_attribute(self):
        ''' The core_base_class should have a working name property and __str__ function.  Testing with a various objects '''
        self.assertEqual(self.my_genome_species.name, 'My Genome Species')
        self.assertEqual(str(self.my_genome_version), 'My Genome')


    def test_core_base_class_should_return_correct_str_for_objects_with_no_name_attribute(self):
        ''' When an object doesn't have an ClassName_name attribute but is declaring it's own name @property '''
        self.assertEqual(str(self.my_feature_location), '1: My Gene: NC_00002.2')


class TemplateAndViewTests(TestCase):
    ''' Class to hold all the test for templates and views '''
    def test_core_entry_page_should_use_template_about_html(self):
        ''' Just make sure we're getting a success status code and hitting the correct template '''
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')