import json
from urllib.request import urlopen

import logging

log = logging.getLogger("app")


def get_pubmed_data(pubmed_id: str | list = None) -> object:
    """Lookup data for a pubmed article"""

    if not pubmed_id:
        return None

    if type(pubmed_id) is list:
        pubmed_id = ",".join([str(id) for id in pubmed_id])

    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={pubmed_id}"
    result = json.loads(urlopen(url).read())

    return result.get("result")
