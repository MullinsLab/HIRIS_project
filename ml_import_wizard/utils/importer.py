from django.conf import settings
from django.apps import apps

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])


importers: dict = {}


class Importer(object):
    """ Class to hold the importers from settings.ML_IMPORT_WIZARD """

    def __init__(self, parent: object = None, name: str = '', type: str = '', description: str = '', long_name: str = '', **settings) -> None:
        """ Initalize the object """
        self.name = name
        self.long_name = long_name
        self.type = type
        self.settings = {}
        self.apps = []


class ImporterApp(object):
    """ Class to hold apps to import into """

    def __init__(self, parent: object = None, name: str='', **settings) -> None:
        """ Initialize the object """
        self.parent = parent
        self.name = name
        self.settings = {}
        self.models = []

        for setting, value in settings.items():
            self.settings[setting] = [value]

        parent.apps.append(self)


class ImporterModel(object):
    """ Holds information about a model that should be imported from files """

    def __init__(self, parent: object = None, name: str = '', **settings) -> None:
        """ Initialize the object """
        self.parent = parent
        self.name = name
        self.settings = {}
        self.fields = []

        parent.models.append(self)


class ImporterField(object):
    """ Holds information about a field that should be imported from files """

    def __init__(self, parent: object = None, name: str = '', **settings):
        """ Initialize the object """
        self.parent = parent
        self.name = name
        self.settings = {}

        parent.fields.append(self)


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
            print(f"Working app parent name: {working_app.parent.name}, parent apps: {working_app.parent.apps}")

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
                working_model: ImporterModel = ImporterModel(parent=working_app, name=model.__name__)

                # Get settingsfor the model and save them in the object, except keys in exclude_keys
                model_settings: dict = app["models"].get(model.__name__, {})
                
                exclude_keys: tuple = ("exclude_fields", "fields")
                for key in filter(lambda key: key not in exclude_keys, model_settings.keys()):
                    working_model.settings[key]=model_settings[key]

                for field in filter(lambda field: field.editable and (field.name not in model_settings.get("exclude_fields", [])), model._meta.get_fields()):
                    working_field: ImporterField = ImporterField(parent=working_model, name=field.name)

                    # Get settings for the field and save them in the object, except keys in exclude_keys
                    field_settings: dict = model_settings.get("fields", {}).get(field.name, {})

                    exclude_keys: tuple = ()
                    for key in filter(lambda key: key not in exclude_keys, field_settings.keys()):
                        working_field.settings[key] = field_settings[key]
    
    # serialized = jsonpickle.encode(importers)
    # print(json.dumps(json.loads(serialized), indent=2))