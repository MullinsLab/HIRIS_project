from django.conf import settings
from django.apps import apps

import logging
log = logging.getLogger(settings.ML_EXPORT_WIZARD['Logger'])

from weakref import proxy

from ml_import_wizard.utils.simple import fancy_name


exporters: dict = {}


class BaseExporter(object):
    """ Base class to inherit from """

    def __init__(self, parent: object = None, name: str = '', **settings) -> None:
        """ Initialise the object """

        if parent: self.parent = proxy(parent)  # Use a weakref so we don't have a circular refrence, defeating garbage collection
        self.name = name
        self.settings = {}
        
        for setting, value in settings.items():
            self.settings[setting] = [value]
            
    @property
    def fancy_name(self) -> str:
        return fancy_name(self.name)
    

class Exporter(BaseExporter):
    """ Class to hold the exporters from settings.ML_EXPORT_WIZARD """

    def __init__(self, *, parent: object = None, name: str = '', type: str = '', description: str = '', long_name: str = '', **settings) -> None:
        """ Initalize the object """

        super().__init__(parent, name, **settings)

        self.long_name = long_name
        self.type = type
        self.apps = []
        self.apps_by_name = {}


class ExporterApp(BaseExporter):
    """ Class to hold apps to export  """

    def __init__(self, *, parent: object = None, name: str='', **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)
        
        self.models = []
        self.models_by_name = {}

        parent.apps.append(self)
        parent.apps_by_name[self.name] = self


class ExporterModel(BaseExporter):
    """ Class to hold the psudomodels to export """

    def __init__(self, *, parent: object = None, name: str='', model: object, **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)

        # Get the Django model so we can do queries against it
        self.model = model

        self.fields = []
        self.fields_by_name = {}

        parent.models.append(self)
        parent.models_by_name[self.name] = self


class ExporterPseudomodel(BaseExporter):
    """ Class to hold the pseudomodels to export """

    def __init__(self, *, parent: object = None, name: str='', **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)

        self.models = []
        self.models_by_name = {}

        parent.models.append(self)
        parent.models_by_name[self.name] = self

    
class ExporterField(BaseExporter):
    """ Class to hold the fields to export """

    def __init__(self, *, parent: object = None, name: str="", field: object = None, **settings) -> None:
        """ Initialise the object"""

        super().__init__(parent, name, **settings)

        # Get the Django field so we can do queries against it
        self.field = field

        parent.fields.append(self)
        parent.fields_by_name[self.name] = self


def setup_exporters() -> None:
    """ Initialize the exporter objects from settings """

    for exporter_setting, exporter_value in settings.ML_EXPORT_WIZARD["Exporters"].items():
        working_exporter = exporters[exporter_setting] = Exporter(
            name = exporter_setting, 
            long_name = exporter_value.get('long_name', ''),
            description = exporter_value.get('description', ''),
        )

        log.debug(f"Working exporter: {working_exporter.name}")

        for app in exporter_value.get("apps", []):
            # Get settingsfor the app and save them in the object, except keys in exclude_keys
            exclude_keys: tuple = ("name", "models", "psudomodels")
            app_settings = {setting: value for setting, value in app.items() if setting not in exclude_keys}
            working_app: ExporterApp = ExporterApp(parent=working_exporter, name=app.get('name', ''), **app_settings)

            for pseudomodel in app.get("pseudomodels", []):
                # Get settingsfor the pseudomodel
                exclude_keys: tuple = ("name", "models")
                pseudomodel_settings = {setting: value for setting, value in pseudomodel.items() if setting not in exclude_keys}

                working_pseudomodel = ExporterPseudomodel(parent=working_app, name=pseudomodel.get("name", ""), **pseudomodel_settings)

                for model in pseudomodel.get("models", []):
                    # Get settings for the model
                    exclude_keys: tuple = ("name", "fields")
                    model_settings = {setting: value for setting, value in model.items() if setting not in exclude_keys}

                    working_model = ExporterModel(parent=working_pseudomodel, name=model.get("name", ""), model=apps.get_model(app_label=app['name'], model_name=model.get("name", "")), **model_settings)

                    for field in model.get("fields", []):
                        working_field = ExporterField(parent=working_model, name=field, field=working_model.model._meta.get_field(field))

                        log.debug(f"Working field: {working_field.name}") 
                        
