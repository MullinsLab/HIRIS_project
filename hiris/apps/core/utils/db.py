import logging
log = logging.getLogger('app')

from django.db import connection

from collections import namedtuple

from ml_export_wizard.utils.exporter import exporters


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

    limit_before_join: dict = {
        "IntegrationFeature": [
            {
                "field": "feature_type_name",
                "value": "gene",
            }
        ]
    }

    return exporters["IntegrationFeatures"].query_count(limit_before_join=limit_before_join, count="DISTINCT:feature_name")