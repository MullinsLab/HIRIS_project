from django.db import models
import re

# Overriding the default ID will make fore a more comprehensible database for non-Django queries.
# Including dates for each object.  It's cheap to store and may be useful at some time.

class CoreBaseModel(models.Model):
    ''' A base class to hold comon methods and attributes.  It's Abstract so Django won't make a table for it
    The # pragma: no cover keeps the lines from being counted in coverage percentages '''
    class Meta:
        abstract = True
    
    added_date = models.DateField(auto_now_add=True, editable=False)
    updated_date = models.DateField(auto_now=True, editable=False)
    
    @property
    def name(self) -> str:
        ''' Returns the specific class name field as name 
        uses explicit name_field if it exists, otherwise defaults to the class name + "_name" '''
        if hasattr(self, 'name_field') and self.name_field:         # type: ignore
            return eval("self." + self.name_field)                  # type: ignore   # pragma: no cover
        else:
            name_list: list[str] = re.sub( r"([A-Z])", r" \1", self.__class__.__name__).split()
            name = '_'.join(name_list)

            return eval("self." + name.lower() + "_name")

    def __str__(self) ->str:
        ''' Generic stringify function.  Most objects will have a name so it's the default. '''
        return self.name

class GenomeSpecies(CoreBaseModel):
    ''' Holds genome hosts.  Initially should contain: Homo Sapiens'''
    genome_species_id = models.BigAutoField(primary_key=True, editable=False)
    genome_species_name = models.CharField(max_length=255, unique=True)
    
    class Meta:
        db_table = "genome_species"


class GenomeVersion(CoreBaseModel):
    ''' Holds Genome top level data '''
    genome_version_id = models.BigAutoField(primary_key=True, editable=False)
    genome_version_name = models.CharField(max_length=255, unique=True)
    # The name of the external_gene_id field in the outside source.  For example, a gene from NCBi would have an external_gene_id_name of 'NCBI_Gene_ID'
    external_gene_id_source = models.CharField(max_length=255, null=True, blank=True)
    genome_species = models.ForeignKey(GenomeSpecies, on_delete=models.CASCADE)

    # name_field = 'genome_version_name'
    
    class Meta:
        db_table = "genome_versions"


class GeneType(CoreBaseModel):
    ''' Hold gene types.  Initially should contain: 
    protein-coding, pseudo, rRNA, tRNA, ncRNA, scRNA, snRNA, snoRNA, miscRNA, transposon, biological-region, lnRNA, SE, eRNA, other '''
    gene_type_id = models.BigAutoField(primary_key=True, editable=False)
    gene_type_name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "gene_types"


class FeatureType(CoreBaseModel):
    ''' Holds feature types, such as Gene, Pseudogene, Exxon, etc. '''
    feature_type_id = models.BigAutoField(primary_key=True, editable=False)
    feature_type_name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'feature_types'


class Feature(CoreBaseModel):
    ''' Holds gene data except for locations '''
    feature_id = models.BigAutoField(primary_key=True, editable=False)
    genome_version = models.ForeignKey(GenomeVersion, on_delete=models.CASCADE)
    feature_name = models.CharField(max_length=255)
    external_gene_id = models.IntegerField(null=True, blank=True)
    feature_type = models.ForeignKey(FeatureType, on_delete=models.CASCADE, null=False)
    gene_type = models.ForeignKey(GeneType, on_delete=models.CASCADE, null=False)

    class Meta:
        db_table = "features"
        unique_together = ['genome_version', 'feature_name']
        indexes = [
            models.Index(fields=['genome_version', 'feature_name']),
            models.Index(fields=['feature_name']),
            models.Index(fields=['genome_version']),
        ]


class FeatureLocation(CoreBaseModel):
    ''' Holds gene location data '''
    feature_location_id = models.BigAutoField(primary_key=True, editable=False)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, editable=False)
    chromosome = models.CharField(max_length=255, null=True)
    landmark = models.CharField(max_length=255, null=True)
    feature_start = models.IntegerField(null=False)
    feature_end = models.IntegerField(null=False)
    feature_orientation = models.CharField(max_length=1, choices=(('F', 'Forward'), ('R', 'Reverse')), null=False)

    @property
    def name(self) -> str:
        ''' Set the name for a GeneLocation to be Gene: Landmark '''
        return f'{self.feature.name}: {self.landmark}'

    class Meta:
        db_table = "feature_locations"
        unique_together = ('feature', 'landmark')
        indexes = [
            models.Index(fields=['feature', 'landmark']),
            models.Index(fields=['landmark']),
            models.Index(fields=['feature', 'chromosome']),
            models.Index(fields=['chromosome']),
        ]
