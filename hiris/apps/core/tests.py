from django.test import TestCase
from django.urls import reverse  

from .models import Genome, GenomeHost, GeneLocation, GeneType, Gene

class ModelTests(TestCase):
    ''' Tests that just test model structure and functions '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up all the test data for ModelTests '''
        
        cls.my_genome_host = GenomeHost.objects.create(genome_host_name='My Genome Host')
        cls.my_genome = Genome.objects.create(genome_name='My Genome', genome_host=cls.my_genome_host)
        cls.my_gene_type = GeneType.objects.create(gene_type_name='My Gene Type')
        cls.my_gene = Gene.objects.create(gene_name='My Gene', genome=cls.my_genome, gene_type=cls.my_gene_type)
        cls.my_gene_location = GeneLocation(gene=cls.my_gene, landmark='chr1', gene_start=1231, gene_end=234234, gene_orientation='F')


    def test_core_base_class_works_correctly(self):
        ''' The core_base_class should have a working name property and __str__ function.  Testing with a various objects '''

        self.assertEqual(self.my_genome_host.name, 'My Genome Host')
        self.assertEqual(str(self.my_genome), 'My Genome')
        self.assertEqual(str(self.my_gene_location), 'My Gene: chr1')

class ViewTests(TestCase):
    ''' Class to hold all the test for views '''
    def test_entry_page_returns_something(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)