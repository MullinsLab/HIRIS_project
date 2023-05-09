from django.conf import settings
from django.apps import AppConfig

import logging
log = logging.getLogger(settings.ML_EXPORT_WIZARD['Logger'])

#from ml_import_wizard.utils.importer import inspect_models


class ExportWizardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_export_wizard'
    verbose_name = 'Mullins Lab Export Wizard'

    # def ready(self) -> None:
    #     """ Initialize the importer objects from settings """

    #     if settings.ML_IMPORT_WIZARD.get("Setup_On_Start", True):
    #         inspect_models()
        