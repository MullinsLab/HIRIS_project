from django.db import models
import re

# Overriding the default ID will make fore a more comprehensible database for non-Django queries.
# Including dates for each object.  It's cheap to store and may be useful at some time.

class CoreBaseModel(models.Model):
    ''' A base class to hold comon methods and attributes.  It's Abstract so Django won't make a table for it
    The # pragma: no cover keeps the lines from being counted in coverage percentages '''
    class Meta:
        abstract = True
    
    added_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True)
    
    @property
    def name(self) -> str:
        ''' Returns the specific class name field as name 
        uses explicit name_field if it exists, otherwise defaults to the class name + "_name" '''
        if hasattr(self, 'name_field') and self.name_field:
            return eval("self." + self.name_field) # pragma: no cover
        else:
            name_list = re.sub( r"([A-Z])", r" \1", self.__class__.__name__).split()
            name = '_'.join(name_list)

            return eval("self." + name.lower() + "_name") # pragma: no cover

    def __str__(self) ->str:
        ''' Generic stringify function.  Most objects will have a name so it's the default. '''
        return self.name # pragma: no cover


class GenomeHosts(CoreBaseModel):
    ''' Holds genome hosts.  Initially should contain: Homo Sapiens'''
    genome_host_id = models.BigAutoField(primary_key=True)
    genome_host_name = models.CharField(max_length=255)
    
    class Meta:
        db_table = "genome_hosts"


class Genome(CoreBaseModel):
    ''' Hold eenome top level data '''
    genome_id = models.BigAutoField(primary_key=True)
    genome_name = models.CharField(max_length=255)
    # The name of the external_gene_id field in the outside source.  For example, a gene from NCBi would have an external_gene_id_name of 'NCBI_Gene_ID'
    external_gene_id_name = models.CharField(max_length=255, null=True, blank=True)
    genome_host = models.ForeignKey(GenomeHosts, on_delete=models.CASCADE)

    class Meta:
        db_table = "genome"


class GeneType(CoreBaseModel):
    ''' Hold gene types.  Initially should contain: 
    protein-coding, pseudo, rRNA, tRNA, ncRNA, scRNA, snRNA, snoRNA, miscRNA, transposon, biological-region, lnRNA, SE, eRNA, other '''
    gene_type_id = models.BigAutoField(primary_key=True)
    gene_type_name = models.CharField(max_length=255)

    class Meta:
        db_table = "gene_type"


class Gene(models.Model):
    ''' Holds gene data except for locations '''
    gene_id = models.BigAutoField(primary_key=True)
    genome = models.ForeignKey(Genome, on_delete=models.CASCADE)
    genome_name = models.CharField(max_length=255)
    external_gene_id = models.IntegerField(null=True, blank=True)
    gene_type = models.ForeignKey(GeneType, on_delete=models.CASCADE)

    class Meta:
        db_table = "gene"

class GeneLocation(CoreBaseModel):
    ''' Holds gene location data'''
    gene_location_id = models.BigAutoField(primary_key=True)
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)
    landmark = models.CharField(max_length=255)
    gene_start = models.IntegerField
    gene_end = models.IntegerField
    gene_orientation = models.CharField(max_length=1, choices=(('F', 'Forward'), ('R', 'Reverse')))

    class Meta:
        db_table = "gene_location"