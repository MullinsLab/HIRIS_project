import logging
log = logging.getLogger('app')

from django.db.models import Q

from hiris.apps.core.models import FeatureLocation


def translate_chromosome_to_accession_id(*, user_input_chromosome: str=None, field_lookup_core__GenomeVersion__genome_version_name: str=None) -> str:
    """ Look up accession id from chromosome name (chr1 ... chrY) for landmarks """

    chromosome: str = str(user_input_chromosome)
    genome_version_name: str = field_lookup_core__GenomeVersion__genome_version_name

    if chromosome.startswith("chr"):
        chromosome = chromosome.replace("chr", "")
    elif len(chromosome) > 1:
        return chromosome
    
    try:
        feature_location: FeatureLocation = FeatureLocation.objects.get(
            ~Q(chromosome=''),
            chromosome__isnull=False,
            feature__feature_name=chromosome, 
            feature__feature_type__feature_type_name="region", 
            feature__genome_version__genome_version_name=genome_version_name,
        )
    except:
        return None

    return feature_location.landmark