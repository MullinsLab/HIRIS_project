import logging
log = logging.getLogger('app')

from hiris.apps.core.models import GenomeVersion


def accession_id_to_chromosome(*, user_input_accession_id: str=None, field_lookup_genome_version_name: str=None) -> str:
    """ Function used to lookup chromosome from accession id for use in importers """

    accession_id: str = user_input_accession_id
    genome_version_name: str = field_lookup_genome_version_name

    

    return "I is a test..."