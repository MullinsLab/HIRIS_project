from django.conf import settings
from django.apps import apps
from django.db.models import ForeignKey

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from weakref import proxy

from ml_import_wizard.utils.simple import fancy_name
from ml_import_wizard.exceptions import UnresolvedInspectionOrder


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

    def __init__(self, *, parent: object = None, name: str = '', type: str = '', description: str = '', long_name: str = '', **settings) -> None:
        """ Initalize the object """
        super().__init__(parent, name, **settings)

        self.long_name = long_name
        self.type = type
        self.apps = []
        self.apps_by_name = {}


class ImporterApp(BaseImporter):
    """ Class to hold apps to import into """

    def __init__(self, *, parent: object = None, name: str='', **settings) -> None:
        """ Initialize the object """
        super().__init__(parent, name, **settings)
        
        self.models = []
        self.models_by_name = {}
        self.models_by_import_order = []

        parent.apps.append(self)
        parent.apps_by_name[self.name] = self


class ImporterModel(BaseImporter):
    """ Holds information about a model that should be imported from files """

    def __init__(self, *, parent: object = None, name: str = '', model: object = '', **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)
        
        # log.debug(f"Model from ImporterModel, Type: {type(model)}, Name: {model.__name__}, My type (ImporterModel): {type(self)}")
        self.model = model # Get the Django model so we can do queries against it
        self.fields = []
        self.fields_by_name = {}

        parent.models.append(self)
        parent.models_by_name[self.name] = self

    def foreign_key_fields(self) -> list:
        """ Returns a list of fields that refer to foreign keys """

        return [field for field in self.fields if field.is_foreign_key()]
    
    def has_foreign_key(self) -> bool:
        """ Returns true if the model has one or more foreign keys """

        if self.foreign_key_fields(): return True
        return False
    
    @property
    def shown_fields(self) -> list:
        return [field for field in self.fields if not field.is_foreign_key()]
    

class ImporterField(BaseImporter):
    """ Holds information about a field that should be imported from files """

    def __init__(self, *, parent: object = None, name: str = '', field: object = '', **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)
        
        self.field = field # Get the Django field so we can do queries against it
        
        parent.fields.append(self)
        parent.fields_by_name[self.name] = self

    def is_foreign_key(self) -> bool:
        """ returns true if the field has a foreign key """

        return isinstance(self.field, ForeignKey)


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
                models = [apps.get_model(app_label=app['name'], model_name=model) 
                          for model in app.get('include_models', [])
                          if model in [app_model.__name__ for app_model in apps.get_app_config(app['name']).get_models()]
                ]

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
                    working_field: ImporterField = ImporterField(parent=working_model, name=field.name, field=field)

                    # Get settings for the field and save them in the object, except keys in exclude_keys
                    field_settings: dict = model_settings.get("fields", {}).get(field.name, {})

                    exclude_keys: tuple = ()
                    for key in filter(lambda key: key not in exclude_keys, field_settings.keys()):
                        working_field.settings[key] = field_settings[key]

            # Step back through the models to put them into the correct order for actual data import
            # do until we have as many models in the models_by_import_order list as in the models list
            while len(working_app.models) > len(working_app.models_by_import_order):
                model_by_import_count = len(working_app.models_by_import_order)
                
                for model in working_app.models:
                    if model in working_app.models_by_import_order:
                        continue

                    # Check to see if the model has any foreign keys
                    foreign_keys = model.foreign_key_fields()
                    if not foreign_keys:
                        working_app.models_by_import_order.append(model)
                        continue
                    
                    dependancy_satisfied = True
                    for field in foreign_keys:
                        if field.field.related_model.__name__ not in [model.name for model in working_app.models_by_import_order]:
                            dependancy_satisfied = False
                            continue
                    
                    if dependancy_satisfied:
                        working_app.models_by_import_order.append(model)
                
                # Raise an exception if we make a loop and haven't increased the number of models in models_by_import_order
                if model_by_import_count >= len(working_app.models_by_import_order):
                    raise UnresolvedInspectionOrder("Order of importing models can't be resolved.  Potential circular ForeignKeys?")
                    
            # log.debug(f"Import Order: {[model.name for model in working_app.models_by_import_order]}")
            # log.debug(f"Raw: {[model.name for model in working_app.models]}")
