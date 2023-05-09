from django.db import models
import re

# Overriding the default ID will make fore a more comprehensible database for non-Django queries.
# Including dates for each object.  It's cheap to store and may be useful at some time.

class CoreBaseModel(models.Model):
    ''' A base class to hold comon methods and attributes.  It's Abstract so Django won't make a table for it
    The # pragma: no cover keeps the lines from being counted in coverage percentages '''
    class Meta:
        abstract = True
    
    added = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    
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
    genome_species_name = models.CharField("Name of the species.", max_length=255, unique=True)
    
    class Meta:
        db_table = "genome_species"


class GenomeVersion(CoreBaseModel):
    ''' Holds Genome top level data '''
    genome_version_id = models.BigAutoField(primary_key=True, editable=False)
    genome_version_name = models.CharField(max_length=255, unique=True)
    # The name of the external_gene_id field in the outside source.  For example, a gene from NCBi would have an external_gene_id_name of 'NCBI_Gene_ID'
    external_gene_id_source = models.CharField(max_length=255, null=True, blank=True)
    genome_species = models.ForeignKey(GenomeSpecies, on_delete=models.CASCADE, related_name='versions')

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
    genome_version = models.ForeignKey(GenomeVersion, on_delete=models.CASCADE, related_name="features")
    feature_name = models.CharField(max_length=255, null=True)
    external_gene_id = models.IntegerField(null=True, blank=True)
    feature_type = models.ForeignKey(FeatureType, on_delete=models.CASCADE, null=False, related_name="features")
    gene_type = models.ForeignKey(GeneType, on_delete=models.CASCADE, null=True, related_name="features")

    class Meta:
        db_table = "features"
        unique_together = ['genome_version', 'feature_name']
        indexes = [
            models.Index(fields=['genome_version', 'feature_name']),
            models.Index(fields=['feature_name']),
            models.Index(fields=['genome_version']),
        ]

    @property
    def name(self) -> str:
        """ cannonical name for Feature.  Since Name can be None needs to include something else """

        return f"{self.feature_id}: {self.feature_name}"


class FeatureLocation(CoreBaseModel):
    ''' Holds gene (and other feature) location data '''
    feature_location_id = models.BigAutoField(primary_key=True, editable=False)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name="feature_locations")
    chromosome = models.CharField(max_length=255, null=True)
    landmark = models.CharField(max_length=255, null=True)
    feature_start = models.IntegerField(null=False)
    feature_end = models.IntegerField(null=False)
    feature_orientation = models.CharField(max_length=1, choices=(('F', 'Forward'), ('R', 'Reverse')), null=False)

    @property
    def name(self) -> str:
        ''' Set the name for a GeneLocation to be Gene: Landmark '''

        # return f'{self.feature.name}: {self.landmark}'
        return f'{self.feature.name}: {self.landmark}'

    class Meta:
        db_table = "feature_locations"
        unique_together = ('feature', 'landmark', 'feature_start', 'feature_end')
        indexes = [
            models.Index(fields=['landmark', 'feature_start', 'feature_end']),
            models.Index(fields=['landmark', 'feature_start']),
            models.Index(fields=['landmark', 'feature_end']),
            models.Index(fields=['landmark']),
            models.Index(fields=['feature_start', 'feature_end']),
            models.Index(fields=['feature_start']),
            models.Index(fields=['feature_end']),
        ]


class DataSet(CoreBaseModel):
    """ Holds core data about a data set """
    data_set_id = models.BigAutoField(primary_key=True, editable=False)
    data_set_name = models.CharField(max_length=255, unique=True)
    genome_version = models.ForeignKey(GenomeVersion, on_delete=models.CASCADE, related_name="data_sets")

    class Meta:
        db_table='data_sets'


class DataSetSource(CoreBaseModel):
    """ Holds data about the source of a data set """
    data_set_source_id = models.BigAutoField(primary_key=True, editable=False)
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, related_name="data_set_sources")
    document_pubmed_id = models.IntegerField(null=True, blank=True)
    document_uri = models.TextField(null=True, blank=True)
    document_citation_url = models.TextField(null=True, blank=True)
    document_citation_doi = models.TextField(null=True, blank=True)
    document_citation_issn = models.CharField(max_length=255, null=True, blank=True)
    document_citation_year = models.IntegerField(null=True, blank=True)
    document_citation_type = models.CharField(max_length=255, null=True, blank=True)
    document_citation_pages = models.CharField(max_length=255, null=True, blank=True)
    document_citation_title = models.TextField(null=True, blank=True)
    document_citation_author = models.TextField(null=True, blank=True)
    document_citation_issue_number = models.CharField(max_length=255, null=True, blank=True)
    document_citation_volume = models.IntegerField(null=True, blank=True)
    document_citation_journal = models.TextField(null=True, blank=True)
    document_citation_citekey = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "data_set_sources"
        unique_together = ("data_set", "document_pubmed_id", "document_uri", "document_citation_url", "document_citation_doi", "document_citation_issn", "document_citation_year", "document_citation_type", "document_citation_pages", "document_citation_title", "document_citation_author", "document_citation_issue_number", "document_citation_volume", "document_citation_journal", "document_citation_citekey")


class Subject(CoreBaseModel):
    """ Holds data about the subject the samples were collected from """
    subject_id = models.BigAutoField(primary_key=True, editable=False)
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, related_name="subjects")
    subject_identifier = models.CharField(max_length=255, null=True, blank=True)

    @property
    def name(self) -> str:
        """ Return Subject:subject_id as name """

        return f"Subject:{self.subject_id}"

    class Meta:
        db_table = "subjects"
        unique_together = ('data_set', 'subject_identifier')


class Sample(CoreBaseModel):
    """ Holds data about a specific sample """
    sample_id = models.BigAutoField(primary_key=True, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="samples")
    culture = models.CharField(max_length=255, null=True, blank=True)
    culture_day = models.IntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    disease = models.CharField(max_length=255, null=True, blank=True)
    genbank = models.CharField(max_length=255, null=True, blank=True)
    original_id = models.CharField(max_length=255, null=True, blank=True)
    provirus_activity = models.CharField(max_length=255, null=True, blank=True)
    pubmed_id = models.IntegerField(null=True, blank=True)
    replicates = models.IntegerField(null=True, blank=True)
    tissue = models.CharField(max_length=255, null=True, blank=True)
    tissue_url = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    visit = models.IntegerField(null=True, blank=True)
    years_on_art = models.FloatField(null=True, blank=True)

    @property
    def name(self) -> str:
        """ Return Sample:sample_id as name """

        return f"Sample:{self.sample_id}"

    class Meta:
        db_table = "samples"
        unique_together = ("subject", "culture", "culture_day", "date", "disease", "genbank", "original_id", "provirus_activity", "pubmed_id", "replicates", "tissue", "tissue_url", "type", "visit", "years_on_art")


class Preparation(CoreBaseModel):
    """ Holds data about how thesample was prepared """
    preparation_id = models.BigAutoField(primary_key=True, editable=False)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name="preparations")
    preparation_description = models.TextField(null=True)

    @property
    def name(self) -> str:
        """ Return Preparation:preparation_id as name """

        return f"Preparation:{self.preparation_id}"
    
    class Meta:
        db_table = "preparations"
        unique_together = ("sample", "preparation_description")

    
class SequencingMethod(CoreBaseModel):
    """ Holds data about how the samples were sequenced """
    sequence_method_id = models.BigAutoField(primary_key=True, editable=False)
    preparation = models.ForeignKey(Preparation, on_delete=models.CASCADE, related_name="sequencing_methods")
    sequencing_method_name = models.CharField(max_length=255, null=True)
    sequencing_method_descripion = models.TextField(null=True)

    class Meta:
        db_table = "sequencing_methods"
        unique_together = ("preparation", "sequencing_method_name", "sequencing_method_descripion")


class IntegrationEnvironment(CoreBaseModel):
    """ Holds data about the environment the sample was collected from """
    integration_environment_id = models.BigAutoField(primary_key=True, editable=False)
    integration_environment_name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "integration_environments"


class Integration(CoreBaseModel):
    """ Holds data about an individual integration """
    integration_id = models.BigAutoField(primary_key=True, editable=False)
    integration_environment = models.ForeignKey(IntegrationEnvironment, on_delete=models.CASCADE, related_name="integrations", null=True)
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, related_name="integrations")
    sequencing_method = models.ForeignKey(SequencingMethod, on_delete=models.CASCADE, related_name="integrations")
    ltr = models.CharField(max_length=2, choices=(('3p', '3p'), ('5p', '5p')), null=True)
    multiple_integration = models.BooleanField(null=True, blank=True)
    multiple_integration_count = models.IntegerField(null=True, blank=True)
    sequence = models.TextField(null=True, blank=True)
    junction_5p = models.IntegerField(null=True, blank=True)
    junction_3p = models.IntegerField(null=True, blank=True)
    sequence_name = models.TextField(null=True, blank=True)
    sequence_uri = models.TextField(null=True, blank=True)
    replicate = models.IntegerField(null=True, blank=True)
    replicates = models.IntegerField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    name_field = "integration_id"

    class Meta:
        db_table = "integrations"


class IntegrationLocation(CoreBaseModel):
    """ Holds data about the locations of a specific integration """
    integration_location_id = models.BigAutoField(primary_key=True, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, related_name="integration_locations")
    feature_location = models.ForeignKey(FeatureLocation, on_delete=models.DO_NOTHING, related_name="integration_locations", null=True)
    landmark = models.CharField(max_length=255)
    location = models.IntegerField()
    orientation_in_landmark = models.CharField(max_length=1, choices=(('F', 'Forward'), ('R', 'Reverse')), null=True)

    class Meta:
        db_table = "integration_locations"
        indexes = [
            models.Index(fields=['landmark', 'location']),
            models.Index(fields=['landmark']),
            models.Index(fields=['location']),
        ]

    @property
    def name(self) -> str:
        """ return landmark: location as name"""

        return f"{self.landmark}: {self.location}"


class BlastInfo(CoreBaseModel):
    """ Holds blast data about an individual location """
    blast_info_id = models.BigAutoField(primary_key=True, editable=False)
    integration_location = models.OneToOneField(IntegrationLocation, on_delete=models.CASCADE)
    identity = models.CharField(max_length=255, null=True, blank=True)
    q_start = models.IntegerField(null=True, blank=True)
    gaps = models.CharField(max_length=255, null=True, blank=True)
    score = models.FloatField(null=True, blank=True)

    name_field = "identity"

    class Meta:
        db_table = "blast_info"