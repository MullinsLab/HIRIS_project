import logging
logger = logging.getLogger('app')

from django.db import connection

from collections import namedtuple


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


def get_sources_count() -> dict:
    """ Returns a count of in-vivo and in-virto observations """

    return generic_query_flat("SELECT COUNT(CASE WHEN ie.integration_environment_name='in vivo' THEN 1 else Null END) AS in_vivo_count, " +
                              "COUNT(CASE WHEN ie.integration_environment_name='in vitro' THEN 1 else Null END) AS in_vitro_count " + 
                              "FROM integrations i, integration_environments ie "+
                              "WHERE i.integration_environment_id=ie.integration_environment_id")