from django.conf import settings
from django.apps import apps

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from weakref import proxy
import json
import jsonpickle

from ml_import_wizard.utils.simple import fancy_name


importers: dict = {}


class BaseImporter(object):
    """ Base class to inherit from """

    def __init__(self, parent: object = None, name: str = '', **settings) -> None:
        if parent: self.parent = proxy(parent)  # Use a weakref so we don't have a circular refrence, defeating garbage collection
        self.name = name
        self.settings = {}
        
        for setting, value in settings.items():
            self.settings[setting] = [value]
            
    @property
    def fancy_name(self) -> str:
        return fancy_name(self.name)
    
        
class Importer(BaseImporter):
    """ Class to hold the importers from settings.ML_IMPORT_WIZARD """

    def __init__(self, parent: object = None, name: str = '', type: str = '', description: str = '', long_name: str = '', **settings) -> None:
        """ Initalize the object """
        super().__init__(parent, name, **settings)

        self.long_name = long_name
        self.type = type
        self.apps = []
        self.apps_by_name = {}


class ImporterApp(BaseImporter):
    """ Class to hold apps to import into """

    def __init__(self, parent: object = None, name: str='', **settings) -> None:
        """ Initialize the object """
        super().__init__(parent, name, **settings)
        
        self.models = []
        self.models_by_name = {}

        parent.apps.append(self)
        parent.apps_by_name[self.name] = self


class ImporterModel(BaseImporter):
    """ Holds information about a model that should be imported from files """

    def __init__(self, parent: object = None, name: str = '', model: object = '', **settings) -> None:
        """ Initialize the object """
        super().__init__(parent, name, **settings)
        
        log.debug(f"Model from ImporterModel, Type: {type(model)}, Name: {model.__name__}, My type (ImporterModel): {type(self)}")
        self.model = model # Get the Django model so we can do queries against it
        self.fields = []
        self.fields_by_name = {}

        parent.models.append(self)
        parent.models_by_name[self.name] = self


class ImporterField(BaseImporter):
    """ Holds information about a field that should be imported from files """

    def __init__(self, parent: object = None, name: str = '', **settings) -> None:
        """ Initialize the object """
        super().__init__(parent, name, **settings)
        
        parent.fields.append(self)
        parent.fields_by_name[self.name] = self


def inspect_models() -> None:
    """ Initialize the importer objects from settings """

    for importer_setting, importer_value in settings.ML_IMPORT_WIZARD["Importers"].items():
        working_importer = importers[importer_setting] = Importer(
            name = importer_setting, 
            long_name = importer_value.get('long_name', ''),
            description = importer_value.get('description', ''),
        )

        for app in importer_value.get("apps", []):
            working_app: ImporterApp = ImporterApp(parent=working_importer, name=app.get('name', ''))

            # Get settingsfor the app and save them in the object, except keys in exclude_keys
            exclude_keys: tuple = ("name", "models")
            for key in filter(lambda key: key not in exclude_keys, app.keys()):
                working_app.settings[key]=app[key]

            # Get explicit list from include_models if it exists
            models: list = []
            if app.get('include_models', []):
                models = filter(lambda model: model.__name__ in app.get('include_models', []), 
                                apps.get_app_config(app['name']).get_models()
                )

            # Get list of models from Django if the models list is still empty, excluding models in "exclude_models"
            if not models:
                models = filter(lambda model: model.__name__ not in app.get("exclude_models", []), 
                                apps.get_app_config(app['name']).get_models()
                )

            for model in models:
                working_model: ImporterModel = ImporterModel(parent=working_app, name=model.__name__, model=model)

                # Get settingsfor the model and save them in the object, except keys in exclude_keys
                model_settings: dict = app["models"].get(model.__name__, {})
                
                exclude_keys: tuple = ("exclude_fields", "fields")
                for key in filter(lambda key: key not in exclude_keys, model_settings.keys()):
                    working_model.settings[key]=model_settings[key]
                
                for field in filter(lambda field: field.editable and (field.name not in model_settings.get("exclude_fields", [])), model._meta.get_fields()):
                    
                    # Skip field if it is a foreign key
                    if field.get_internal_type() in ('ForeignKey'):
                        continue
                    
                    working_field: ImporterField = ImporterField(parent=working_model, name=field.name)

                    # Get settings for the field and save them in the object, except keys in exclude_keys
                    field_settings: dict = model_settings.get("fields", {}).get(field.name, {})

                    exclude_keys: tuple = ()
                    for key in filter(lambda key: key not in exclude_keys, field_settings.keys()):
                        working_field.settings[key] = field_settings[key]