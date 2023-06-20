import logging
log = logging.getLogger('app')

from django.db import connection

from collections import namedtuple

from ml_export_wizard.utils.exporter import exporters
from hiris.apps.core.models import Publication

def generic_query(sql: str = None, no_return: bool=False) -> list[dict]|None:
    """ Reuturns a list of namedtuples with the data """

    with connection.cursor() as cursor:
        cursor.execute(sql)

        if no_return:
            return None
        
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

    query = exporters["Integrations"].query(group_by="integration_environment_name")

    return query.query_count()


def get_genes_count() -> int:
    """ Returns a count of unique genes """

    query = exporters["IntegrationFeatures"].query(
        where_before_join={
            "IntegrationFeature": [
                {
                    "field": "feature_type_name",
                    "value": "gene",
                }
            ]
        },
        count="DISTINCT:feature_name"
    )

    return query.query_count()


def get_data_sources() -> list:
    """ Get a list of the sources grouped by in vitro or in vivo """

    query = exporters["Integrations"].query(
        extra_field = {
            "column_name": "count_of_integrations",
            "function": "count",
        },
        group_by = ["data_set_name", "integration_environment_name", "publication_pubmed_id", "publication_id"],
        order_by = "data_set_name",
    )

    sources =query.get_dict_list()

    for source in [source for source in sources if source["publication_pubmed_id"]]:
        publication = Publication.objects.get(publication_id=source["publication_id"])
        
        source["first_author"] = publication.publication_data.get(key="first_author").value
        source["title"] = publication.publication_data.get(key="title").value

    return sources


def get_summary_by_gene(*, limit: int=None, order_output: bool=None) -> list:
    """ Get a list of genes with associated data """

    if order_output:
        order_by: list = [{"field": "subjects", "order": "DESC"}, {"field": "unique_sites", "order": "DESC"}, {"field": "total_in_gene", "order": "DESC"}]
    else:
        order_by: None

    query = exporters["SummaryByGene"].query(
        where  = [
            {
                "field": "subjects",
                "not_null": True,
            },
            {
                "field": "feature_name",
                "not_null": True,
            }
        ],
        order_by = order_by,
        limit = limit,
    )
        
    return query.get_dict_list()


def process_integration_feature_links() -> None:
    """ Execute the query that links Integrations to Features """

    sql = """INSERT INTO integration_features (added, updated, integration_location_id, feature_location_id, feature_type_name)
SELECT now(), now(), integration_location_id, feature_locations.feature_location_id, feature_types.feature_type_name
from integration_locations
	join integrations
		using (integration_id)
	join feature_locations
		on 
			CASE 
				WHEN (integration_locations.orientation_in_landmark='F' AND (integrations.ltr='5p' OR integrations.ltr IS NULL))  
					OR (integration_locations.orientation_in_landmark='R' AND (integrations.ltr='3p' OR integrations.ltr IS NULL)) 
				THEN integration_locations.location > feature_locations.feature_start AND integration_locations.location <= feature_locations.feature_end 
				WHEN (integration_locations.orientation_in_landmark='R' AND (integrations.ltr='5p' OR integrations.ltr IS NULL))  
					OR (integration_locations.orientation_in_landmark='F' AND (integrations.ltr='3p' OR integrations.ltr IS NULL)) 
				THEN integration_locations.location >= feature_locations.feature_start AND integration_locations.location < feature_locations.feature_end 
			END 
			AND feature_locations.landmark = integration_locations.landmark
	join features using (feature_id)
	join feature_types using (feature_type_id)
WHERE integration_location_id NOT IN (SELECT integration_location_id FROM integration_features);"""

    return generic_query(sql=sql, no_return=True)