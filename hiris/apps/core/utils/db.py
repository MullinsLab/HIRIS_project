import logging
log = logging.getLogger('app')

from django.db import connection

from collections import namedtuple

from ml_export_wizard.utils.exporter import exporters
from hiris.apps.core.models import Publication

def generic_query(sql: str = None) -> list[dict]:
    """ Reuturns a list of namedtuples with the data """

    with connection.cursor() as cursor:
        cursor.execute(sql)

        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def generic_query_flat(sql: str = None) -> namedtuple:
    """ Returns a single namedtuple with the data """

    result: dict = generic_query(sql=sql)

    if not result:
        return None
    
    return result[0]


def get_environments_count() -> dict:
    """ Returns a count of in-vivo and in-virto observations """

    return exporters["Integrations"].query_count(group_by="integration_environment_name")


def get_genes_count() -> int:
    """ Returns a count of unique genes """

    where_before_join: dict = {
        "IntegrationFeature": [
            {
                "field": "feature_type_name",
                "value": "gene",
            }
        ]
    }

    return exporters["IntegrationFeatures"].query_count(where_before_join=where_before_join, count="DISTINCT:feature_name")


def get_data_sources() -> list:
    """ Get a list of the sources grouped by in vitro or in vivo """

    extra_field: dict = {
        "column_name": "count_of_integrations",
        "function": "count",
    }

    group_by: list = ["data_set_name", "integration_environment_name", "publication_pubmed_id", "publication_id"]

    sources = exporters["Integrations"].query_rows(group_by=group_by, extra_field=extra_field, order_by="data_set_name")

    # log.debug(sources)

    for source in [source for source in sources if source["publication_pubmed_id"]]:
        log.debug(source["publication_pubmed_id"])
        publication = Publication.objects.get(publication_id=source["publication_id"])
        source["first_author"] = publication.publication_data.filter(key="first_author")[0].value
        source["title"] = publication.publication_data.filter(key="title")[0].value

    return sources


def get_summary_by_gene() -> list:
    """ Get a list of genes with associated data """

    where_before_join: dict = {
        "IntegrationFeature": [
            {
                "field": "feature_type_name",
                "value": "gene",
            }
        ]
    }

    extra_field: list = [
        {
            "column_name": "subjects",
            "function": "case",
            "source_field": "integration_environment_name",
            "when": {
                "condition": "in vivo",
                "extra_field": {
                    "function": "count",
                    "source_field": "subject_identifier",
                    "distinct": True,
                },
            }
        },
        {
            "column_name": "unique_sites",
            "function": "count",
            "source_field": ["landmark", "location"]
        },
        {
            "column_name": "proliferating_sites",
            "function": "count",
            "source_field": ["landmark", "location"],
            "filter": [
                {
                    "field": "multiplicity",
                    "operator": ">=",
                    "value": 2,
                },
            ]
        },
        {
            "column_name": "total_in_gene",
            "function": "sum",
            "source_field": "multiplicity",
            "cast": "int",
        },
    ]

    group_by: list = ["integration_environment_name", "feature_name", "gene_type_name"]

    return exporters["IntegrationFeaturesSummary"].query_rows(where_before_join=where_before_join, group_by=group_by, extra_field=extra_field)