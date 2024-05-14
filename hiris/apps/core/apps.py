import logging
log = logging.getLogger('app')

from django.apps import AppConfig

from hiris.apps.core import managers


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hiris.apps.core'

    def ready(self): 
        from hiris.apps.core import signals

        from hiris.apps.core.models import DataSet, GenomeSpecies, GenomeVersion, GeneType, Feature, FeatureType
        managers.models_graph = managers.ModelsGraph(app="core", start_with=DataSet, initial_path_string="", exclude_models=[GenomeSpecies, GenomeVersion, GeneType, Feature, FeatureType], exclude_from_path=[])
 