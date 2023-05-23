import json
from urllib.request import urlopen

import logging
log = logging.getLogger('app')


def get_pubmed_data(pubmed_id: str=None) -> object:
    """ Lookup data for a pubmed article """

    if not pubmed_id:
        return None
    
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={pubmed_id}"

    return json.loads(urlopen(url).read())
