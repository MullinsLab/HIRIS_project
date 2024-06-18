import logging
log = logging.getLogger('app')

from django.db import connection

from collections import namedtuple
from functools import lru_cache

from ml_export_wizard.utils.exporter import exporters # type: ignore

from hiris.apps.core.models import Publication, Feature, GenomeVersion, LandmarkChromosome
from hiris.utils import current_user

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


def get_current_user_external_value() -> dict:
    """ Returns the external values for the current user """

    if user := current_user():
        return {"user_id": user.pk}

    return {}


def get_most_interesting(environment: str=None, data_set_limit: list=None) -> Feature:
    """ Returns the most interesting gene for an environment """

    query = exporters["SummaryByGene"].query(
        external_values=get_current_user_external_value(),
        extra_field = [
            {
                "column_name": "interestingness",
                "formula": '"total_in_gene"::numeric/"unique_sites"::numeric/coalesce("subjects"::numeric, 1)',
            },
        ],
        group_by = ["feature_name", "total_in_gene", "unique_sites", "subjects"],
        order_by = [
            {"formula": '"total_in_gene"::numeric/"unique_sites"::numeric/coalesce("subjects"::numeric, 1)::numeric'}, 
            {"formula": 'coalesce("subjects", 1)', "order": "DESC"},
            {"field": "unique_sites", "order": "DESC"},
            {"field": "total_in_gene", "order": "DESC"}
        ],
        where = [
            {
                "field": "integration_environment_name",
                "value": environment,
            },
            {
                "field": "feature_name",
                "not_null": True,
            }
        ],
        limit = 1,
    )

    if data_set_limit:
        query.where.append({
            "field": "data_set_name",
            "value": data_set_limit,
            "operator": "in",
        })
    
    return Feature.objects.get(feature_name=query.get_single_dict()["feature_name"])


def get_environments_count() -> dict:
    """ Returns a count of in-vivo and in-virto observations """

    query = exporters["Integrations"].query(external_values=get_current_user_external_value(), group_by="integration_environment_name")

    return query.query_count()


def get_genes_count() -> int:
    """ Returns a count of unique genes """

    query = exporters["IntegrationFeatures"].query(
        external_values=get_current_user_external_value(),
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
        external_values=get_current_user_external_value(),
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


def get_summary_by_gene(*, limit: int=None, order_output: bool=None, data_set_limit: list=None) -> list:
    """ Get a list of genes with associated data """

    order_by: list[dict[str: str]] = None
    if order_output:
        order_by = [{"field": "subjects", "order": "DESC"}, {"field": "unique_sites", "order": "DESC"}, {"field": "total_in_gene", "order": "DESC"}]
    else:
        order_by: None

    query = exporters["SummaryByGene"].query(
        external_values=get_current_user_external_value(),
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

    if data_set_limit:
        query.where_before_join = {
            "DataSet": [{
                "field": "data_set_id",
                "value": data_set_limit,
                "operator": "in",
            }],
        }
        
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


@lru_cache(maxsize=1000)
def get_chromosome_from_landmark(*, landmark: str, genome_version: str|GenomeVersion) -> str:
    """ Returns the chromosome from a landmark """

    log.debug(f"Genome version name: {genome_version}, Landmark: {landmark}")

    if type(genome_version) == str:
        try:
            chromosome = GenomeVersion.objects.get(genome_version_name=genome_version).landmark_chromosomes.get(landmark=landmark).chromosome_name
        except LandmarkChromosome.DoesNotExist:
            chromosome = None

    elif type(genome_version) == GenomeVersion:
        try:
            genome_version.landmark_chromosomes.get(landmark=landmark).chromosome_name
        except LandmarkChromosome.DoesNotExist:
            chromosome = None
            
    return chromosome


def genes_with_integrations() -> list:
    """ Returns a list of genes with integrations """

    query = exporters["IntegrationFeatures"].query()
    query.external_value=get_current_user_external_value()
    query.group_by = "feature_name"
    query.where_before_join = {
        "IntegrationFeature": [
            {
                "field": "feature_type_name",
                "value": "gene",
            },
        ],
    }
    query.order_by = "feature_name"

    return query.get_value_list()