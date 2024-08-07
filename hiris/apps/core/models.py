import logging
log = logging.getLogger("app")

import re

from django.db import models
from django.contrib.auth.models import User, Group

from hiris.utils import get_anonymous_user, get_everyone_group
from hiris.apps.core.managers import DataSetLimitingManager

# Overriding the default ID will make for a more comprehensible database for non-Django queries.
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
        """ Returns the specific class name field as name 
        uses explicit name_field if it exists, otherwise defaults to the class name + "_name" """

        if hasattr(self, 'name_field') and self.name_field:         # type: ignore
            return str(getattr(self, self.name_field))              # type: ignore   # pragma: no cover
        else:
            name_list: list[str] = re.sub( r"([A-Z])", r" \1", self.__class__.__name__).split()
            name = '_'.join(name_list)

            #return eval("self." + name.lower() + "_name")
            return str(getattr(self, f"{name.lower()}_name"))

    def __str__(self) ->str:
        ''' Generic stringify function.  Most objects will have a name so it's the default. '''

        return self.name


class DataSetLimitingModel(CoreBaseModel):
    """ Holds the managers for models that need to be limited by cohort.  
    It's Abstract so Django won't make a table for it """

    objects = DataSetLimitingManager()
    objects_raw = models.Manager()

    class Meta:
        abstract = True


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


class FeatureLocation(DataSetLimitingModel):
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


class DataSet(DataSetLimitingModel):
    """ Holds core data about a data set """

    data_set_id = models.BigAutoField(primary_key=True, editable=False)
    data_set_name = models.CharField(max_length=255, unique=True)
    genome_version = models.ForeignKey(GenomeVersion, on_delete=models.CASCADE, related_name="data_sets")
    groups = models.ManyToManyField(Group, related_name="data_sets", blank=True)
    users = models.ManyToManyField(User, related_name="data_sets", blank=True)
    
    class Meta:
        db_table = "data_sets"
        ordering = ["data_set_name"]

    def str(self) -> str:
        return self.data_set_name

    @property
    def access_control(self) -> str:
        """ Returns who has access to the data set """

        if get_anonymous_user() in self.users.all():
            return "Public"
        
        if get_everyone_group() in self.groups.all():
            return "Everyone"
        
        else:
            return "Specific"
        
    @access_control.setter
    def access_control(self, value: str) -> None:
        """ Set the access control for the data set """

        if self.access_control == value:
            return

        if value == "Public":
            self.groups.add(get_everyone_group())
            self.users.add(get_anonymous_user())
        
        elif value == "Everyone":
            self.groups.add(get_everyone_group())
            self.users.remove(get_anonymous_user())
        
        elif value == "Specific":
            self.groups.remove(get_everyone_group())
            self.users.remove(get_anonymous_user())

        self.save()


class DataSetSource(DataSetLimitingModel):
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

    @property
    def name(self) -> str:
        """ cannonical name for DataSetSourcesince it doesn't have a good name """

        return f"Data Set: {self.pk}"

    class Meta:
        db_table = "data_set_sources"
        unique_together = ("data_set", "document_pubmed_id", "document_uri", "document_citation_url", "document_citation_doi", "document_citation_issn", "document_citation_year", "document_citation_type", "document_citation_pages", "document_citation_title", "document_citation_author", "document_citation_issue_number", "document_citation_volume", "document_citation_journal", "document_citation_citekey")


class Publication(DataSetLimitingModel):
    """ Holds information about the publications that the data comes from """

    publication_id = models.BigAutoField(primary_key=True, editable=False)
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE, related_name="publications")
    publication_pubmed_id = models.IntegerField(null=True)

    name_field = "publication_pubmed_id"

    class Meta:
        db_table = "publications"
        unique_together = ("data_set", "publication_pubmed_id")


class PublicationData(DataSetLimitingModel):
    """ Holds information about publications, one row per key/value pair """

    publication_data_id = models.BigAutoField(primary_key=True, editable=False)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="publication_data")
    key = models.CharField(max_length=255)
    value = models.JSONField()

    class Meta:
        db_table = "publication_data"
        unique_together = ("publication", "key")
        
        indexes = [
            models.Index(fields=["publication", "key", "value"]),
            models.Index(fields=["key", "value"]),
            models.Index(fields=["key"]),
            models.Index(fields=["publication"]),
        ]


class Subject(DataSetLimitingModel):
    """ Holds data about the subject the samples were collected from """

    subject_id = models.BigAutoField(primary_key=True, editable=False)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="subjects")
    subject_identifier = models.CharField(max_length=255, null=True, blank=True)

    @property
    def name(self) -> str:
        """ Return Subject:subject_id as name """

        return f"Subject:{self.subject_id}"

    class Meta:
        db_table = "subjects"
        unique_together = ('publication', 'subject_identifier')


class SubjectData(DataSetLimitingModel):
    """ Holds random data about the subject """

    subject_data_id = models.BigAutoField(primary_key=True, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="subject_data")
    key = models.CharField(max_length=255, null=False, blank=False)
    value = models.JSONField(null=False, blank=False)

    def __str__(self) -> str:
        """ Return key: value as string """

        return f"{self.key}: {self.value}"

    class Meta: 
        db_table = "subject_data"
        unique_together = ('subject', 'key')

        indexes = [
            models.Index(fields=["subject", "key", "value"]),
            models.Index(fields=["key", "value"]),
            models.Index(fields=["key"]),
            models.Index(fields=["subject"]),
        ]

class Sample(DataSetLimitingModel):
    """ Holds data about a specific sample """

    sample_id = models.BigAutoField(primary_key=True, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="samples")
    sample_name = models.CharField(max_length=255, null=True, blank=True)

    @property
    def name(self) -> str:
        """ Return Sample:sample_id as name """

        return f"Sample:{self.sample_id}"

    class Meta:
        db_table = "samples"
    

class SampleData(DataSetLimitingModel):
    """ Holds random data about the sample """

    sample_data_id = models.BigAutoField(primary_key=True, editable=False)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name="sample_data")
    key = models.CharField(max_length=255, null=False, blank=False)
    value = models.JSONField(null=False)

    class Meta:
        db_table = "sample_data"
        unique_together = ("sample", "key")

        indexes = [
            models.Index(fields=["sample", "key", "value"]),
            models.Index(fields=["key", "value"]),
            models.Index(fields=["key"]),
            models.Index(fields=["sample"]),
        ]


class Preparation(DataSetLimitingModel):
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

    
class SequencingMethod(DataSetLimitingModel):
    """ Holds data about how the samples were sequenced """

    sequencing_method_id = models.BigAutoField(primary_key=True, editable=False)
    preparation = models.ForeignKey(Preparation, on_delete=models.CASCADE, related_name="sequencing_methods")
    sequencing_method_name = models.CharField(max_length=255, null=True)
    sequencing_method_descripion = models.TextField(null=True)

    class Meta:
        db_table = "sequencing_methods"
        unique_together = ("preparation", "sequencing_method_name", "sequencing_method_descripion")


class IntegrationEnvironment(DataSetLimitingModel):
    """ Holds data about the environment the sample was collected from """

    integration_environment_id = models.BigAutoField(primary_key=True, editable=False)
    integration_environment_name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "integration_environments"


class Integration(DataSetLimitingModel):
    """ Holds data about an individual integration """

    integration_id = models.BigAutoField(primary_key=True, editable=False)
    integration_environment = models.ForeignKey(IntegrationEnvironment, on_delete=models.CASCADE, related_name="integrations", null=True)
    sequencing_method = models.ForeignKey(SequencingMethod, on_delete=models.CASCADE, related_name="integrations")
    integration_name = models.CharField(max_length=255, null=True, blank=True)
    ltr = models.CharField(max_length=4, choices=(('3p', '3p'), ('5p', '5p'), ("both", "both")), null=True)
    multiple_integration = models.BooleanField(null=True, blank=True)
    multiple_integration_count = models.IntegerField(null=True, blank=True)
    sequence = models.TextField(null=True, blank=True)
    junction_5p = models.IntegerField(null=True, blank=True)
    junction_3p = models.IntegerField(null=True, blank=True)
    sequence_name = models.TextField(null=True, blank=True)
    sequence_uri = models.TextField(null=True, blank=True)
    ltr_sequence = models.TextField(null=True, blank=True)
    breakpoint_sequence = models.TextField(null=True, blank=True)
    umi_sequence = models.TextField(null=True, blank=True)
    ltr_sequence_5p = models.TextField(null=True, blank=True)
    breakpoint_sequence_5p = models.TextField(null=True, blank=True)
    umi_sequence_5p = models.TextField(null=True, blank=True)
    ltr_sequence_3p = models.TextField(null=True, blank=True)
    breakpoint_sequence_3p = models.TextField(null=True, blank=True)
    umi_sequence_3p = models.TextField(null=True, blank=True)
    provirus_sequence = models.TextField(null=True, blank=True)
    replicate = models.IntegerField(null=True, blank=True)
    replicates = models.IntegerField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    name_field = "integration_id"

    class Meta:
        db_table = "integrations"
        indexes = [
            models.Index(fields=['ltr']),
        ]


class IntegrationLocation(DataSetLimitingModel):
    """ Holds data about the locations of a specific integration """

    integration_location_id = models.BigAutoField(primary_key=True, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, related_name="integration_locations")
    feature_locations = models.ManyToManyField(FeatureLocation, related_name="integration_locations", through="IntegrationFeature", editable=False)
    
    landmark = models.CharField(max_length=255)
    location = models.IntegerField()
    breakpoint_landmark = models.CharField(max_length=255, null=True)
    breakpoint_location = models.IntegerField(null=True)
    
    landmark_5p = models.CharField(max_length=255, null=True)
    location_5p = models.IntegerField(null=True)
    breakpoint_landmark_5p = models.CharField(max_length=255, null=True)
    breakpoint_location_5p = models.IntegerField(null=True)

    landmark_3p = models.CharField(max_length=255, null=True)
    location_3p = models.IntegerField(null=True)
    breakpoint_landmark_3p = models.CharField(max_length=255, null=True)
    breakpoint_location_3p = models.IntegerField(null=True)

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


class IntegrationFeature(DataSetLimitingModel):
    """ Holds the links between Integrations and Features """

    integration_feature_id = models.BigAutoField(primary_key=True)
    integration_location = models.ForeignKey(IntegrationLocation, on_delete=models.CASCADE)
    feature_location = models.ForeignKey(FeatureLocation, on_delete=models.DO_NOTHING)
    feature_type_name = models.CharField(max_length=255)

    class Meta:
        db_table = "integration_features"
        unique_together = ['integration_location', 'feature_location']
        indexes = [
            models.Index(fields=['integration_location']),
            models.Index(fields=['feature_location']),
        ]


class BlastInfo(DataSetLimitingModel):
    """ Holds blast data about an individual location """

    blast_info_id = models.BigAutoField(primary_key=True, editable=False)
    integration_location = models.OneToOneField(IntegrationLocation, on_delete=models.CASCADE, related_name="blast_info")
    identity = models.CharField(max_length=255, null=True, blank=True)
    q_start = models.IntegerField(null=True, blank=True)
    gaps = models.CharField(max_length=255, null=True, blank=True)
    score = models.FloatField(null=True, blank=True)

    name_field = "identity"

    class Meta:
        db_table = "blast_info"


class LandmarkChromosome(DataSetLimitingModel):
    """ Holds data about the chromosomes of the landmark """
    
    landmark_chromosome_id = models.BigAutoField(primary_key=True, editable=False)
    genome_version = models.ForeignKey(GenomeVersion, on_delete=models.CASCADE, related_name="landmark_chromosomes")
    landmark = models.CharField(max_length=255)
    chromosome_name = models.CharField(max_length=255)

    class Meta:
        db_table = "landmark_chromosomes"
        unique_together = ["genome_version", "landmark"]