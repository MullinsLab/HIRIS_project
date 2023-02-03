from django.test import TestCase
from .models import Genome, GenomeHost

class ModelTests(TestCase):
    ''' Tests that just test model structure and functions '''
    def test_core_base_class_works_correctly(self):
        ''' The core_base_class should have a working name property and __str__ function.  Testing with a Genome object '''
        my_genome_host = GenomeHost(genome_host_name='My Genome Host')
        my_genome_host.save()

        my_genome = Genome(genome_name='My Genome', genome_host=my_genome_host)
        my_genome.save()

        self.assertEqual(str(my_genome_host), 'My Genome Host')
        self.assertEqual(str(my_genome), 'My Genome')