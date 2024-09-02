import logging
log = logging.getLogger('app')

import json

from django.db import IntegrityError, transaction

from hiris.apps.core.utils.db import process_integration_feature_links
from hiris.apps.core.models import Publication, PublicationData
from hiris.apps.core.utils.network import get_pubmed_data


def process_after_import() -> None:
    """ Link the integrations to features and get publication data from Pubmed.  Needs to run after each import """

    fill_publication_data()
    log.info("Completed filling publication data.")

    process_integration_feature_links()
    log.info("Completed processing integration feature links.")


def fill_publication_data() -> None:
    """ Fills the PublicationData objects for Publications that don't have them yet """

    publications: list[Publication] = Publication.objects.filter(publication_data=None, publication_pubmed_id__isnull=False)
    data: dict = get_pubmed_data(pubmed_id=[publication.publication_pubmed_id for publication in publications])


    for publication in publications:
        # Use a transaction so each source row gets saved or not
        try:
            with transaction.atomic():
                if str(publication.publication_pubmed_id) not in data:
                    continue

                publication_data: dict = data[str(publication.publication_pubmed_id)]

                PublicationData.objects.bulk_create([
                    PublicationData(publication=publication, key="first_author", value=publication_data['authors'][0]['name']),
                    PublicationData(publication=publication, key="title", value=publication_data['title'])
                ])
            
        except IntegrityError as err:
            log.debug(err)