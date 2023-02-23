from django.test import TestCase
from django.urls import reverse  

from hiris.apps.core.models import Genome, GenomeSpecies, GeneLocation, GeneType, Gene

class ModelTests(TestCase):
    ''' Tests that just test model structure and functions '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up all the test data for ModelTests '''
        cls.my_genome_species = GenomeSpecies.objects.create(genome_species_name='My Genome Species')
        cls.my_genome = Genome.objects.create(genome_version_name='My Genome', genome_species=cls.my_genome_species)
        cls.my_gene_type = GeneType.objects.create(gene_type_name='My Gene Type')
        cls.my_gene = Gene.objects.create(gene_name='My Gene', genome=cls.my_genome, gene_type=cls.my_gene_type)
        cls.my_gene_location = GeneLocation(gene=cls.my_gene, landmark='chr1', gene_start=1231, gene_end=234234, gene_orientation='F')


    def test_core_base_class_should_return_names_that_match_objects_name_attribute(self):
        ''' The core_base_class should have a working name property and __str__ function.  Testing with a various objects '''
        self.assertEqual(self.my_genome_species.name, 'My Genome Species')
        self.assertEqual(str(self.my_genome), 'My Genome')


    def test_core_base_class_should_return_correct_str_for_objects_with_no_name_attribute(self):
        ''' When an object doesn't have an ClassName_name attribute but is declaring it's own name @property '''
        self.assertEqual(str(self.my_gene_location), 'My Gene: chr1')


class TemplateAndViewTests(TestCase):
    ''' Class to hold all the test for templates and views '''
    def test_core_entry_page_should_use_template_about_html(self):
        ''' Just make sure we're getting a success status code and hitting the correct template '''
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.django-html')