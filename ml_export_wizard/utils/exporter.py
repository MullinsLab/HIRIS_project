from django.conf import settings
from django.apps import apps
from django.db.models import ForeignKey, ManyToOneRel

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
            self.settings[setting] = value
            
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

    def sql(self, *args, **kwargs) -> str:
        """ Returns a raw SQL query that would be used to generate the exporter data"""
        
        sql: str = ""
        sql_dict: dict[str: str] = {}

        for app in self.apps:
            sql_dict = merge_sql_dicts(sql_dict, app._sql_dict())

        if sql_dict.get("select"):
            sql += f"SELECT {sql_dict['select']} "

        if sql_dict.get("from"):
            sql += f"FROM {sql_dict['from']} "

        if sql_dict.get("where"):
            sql += f"WHERE {sql_dict['where']} "

        return sql


class ExporterApp(BaseExporter):
    """ Class to hold apps to export  """

    def __init__(self, *, parent: object = None, name: str='', **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)
        
        self.models = []
        self.models_by_name = {}

        parent.apps.append(self)
        parent.apps_by_name[self.name] = self

    def _sql_dict(self) -> dict[str: str]:
        """ Create an SQL_Dict for the query bits from this app"""

        sql_dict: dict[str: str] = {}

        for model in self.models:
            sql_dict = merge_sql_dicts(sql_dict, model._sql_dict())

        return sql_dict


class ExporterModel(BaseExporter):
    """ Class to hold the psudomodels to export """

    def __init__(self, *, parent: object = None, name: str='', model: object, **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)

        self.model = model

        self.fields = []
        self.fields_by_name = {}

        parent.models.append(self)
        parent.models_by_name[self.name] = self

    @property
    def table(self) -> str:
        """ returns the db table name to query against """

        return self.model.objects.model._meta.db_table

    def _sql_dict(self, *, table_name: str = None) -> dict[str: str]:
        """ Create an SQL_Dict for the query bits from this model"""

        sql_dict: dict[str: str] = {}
        sql_dict["from"] = self.table

        for field in self.fields:
            sql_dict = merge_sql_dicts(sql_dict, field._sql_dict(table_name=table_name))
            
        return sql_dict


class ExporterPseudomodel(BaseExporter):
    """ Class to hold the pseudomodels to export """

    def __init__(self, *, parent: object = None, name: str='', **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)

        self.models = []
        self.models_by_name = {}

        parent.models.append(self)
        parent.models_by_name[self.name] = self

    def _sql_dict(self) -> dict[str: str]:
        """ Create an SQL_Dict for the query bits from this pseudomodel"""

        sql_dict: dict[str: str] = {}

        for model in self.models:
            sql_dict = merge_sql_dicts(sql_dict, model._sql_dict(table_name=self.name))

        if self.settings.get("sql_from"):
            sql_dict["from"] = self._replace_tags(self.settings["sql_from"])
            sql_dict["from"] = f"(SELECT {sql_dict['select_no_table']} {sql_dict['from']}) as {self.name}"

        return sql_dict
    
    def _replace_tags(self, value: str = None) -> str:
        """ Replace the tags in the value string.  e.g. {Model:table} => table_name """ 

        if not value or type(value) is not str:
            return value

        for model in self.models:
            value = value.replace(f"{{{model.name}:table}}", model.table)

            fields: str = ""
            for field in model.fields:
                fields = ", ".join(filter(None, (fields, field.field.column)))

            if fields:
                value = value.replace(f"{{{model.name}:fields}}", fields)

        return value

    
class ExporterField(BaseExporter):
    """ Class to hold the fields to export """

    def __init__(self, *, parent: object = None, name: str="", field: object = None, **settings) -> None:
        """ Initialise the object"""

        super().__init__(parent, name, **settings)

        self.field = field

        parent.fields.append(self)
        parent.fields_by_name[self.name] = self

    @property
    def column(self) -> str:
        """ returns the name of the DB column for the field"""

        return self.field.column

    def is_foreign_key(self) -> bool:
        """ returns True if the field has a foreign key """

        return isinstance(self.field, ForeignKey)
    
    def _sql_dict(self, *, table_name: str = None) -> dict[str: str]:
        """ Create an SQL_Dict for the query bits from this field"""

        if self.settings.get("join_only"):
            return {}

        sql_dict: dict[str: str] = {}
        
        if table_name:
            sql_dict["select"] = f"{table_name}.{self.column}"
        else:
            sql_dict["select"] = f"{self.parent.table}.{self.column}"

        sql_dict["select_no_table"] = self.column

        return sql_dict


def merge_sql_dicts(dict1: dict = None, dict2: dict = None) -> dict[str: str]:
    """ Merge SQL dictionaries together """

    if dict1 is None and dict2 is None:
        return None
    
    if dict1 is not None and dict2 is None:
        return dict1.copy()

    if dict1 is None and dict2 is not None:
        return dict2.copy()

    merged: dict[str: str] = {}
    mergers: dict[str: str] = {"select": ", ",
                               "select_no_table": ", ",
                               "from": ", ",
                               "where": " AND ",
                               "group_by": ", ",
                               "having": " AND "
                               }

    for key, value in mergers.items():
        if key not in dict1 and key not in dict2:
            merged[key] = ""
        elif key in dict1 and key not in dict2:
            merged[key] = dict1[key]
        elif key in dict2 and key not in dict1:
            merged[key] = dict2[key]
        else:
            merged[key] = value.join(filter(None, (dict1[key], dict2[key])))

    return merged


def setup_exporters() -> None:
    """ Initialize the exporter objects from settings """

    for exporter_setting, exporter_value in settings.ML_EXPORT_WIZARD["Exporters"].items():
        exclude_keys: tuple = ("name", "description", "apps")
        exporter_settings = {setting: value for setting, value in exporter_value.items() if setting not in exclude_keys}
        working_exporter = exporters[exporter_setting] = Exporter(name = exporter_setting, long_name = exporter_value.get('long_name', ''), description = exporter_value.get('description', ''), **exporter_settings)

        for app in exporter_value.get("apps", []):
            # Get settings for the app and save them in the object, except keys in exclude_keys
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

                    for field in model.get("join_only_fields", []):
                        working_field = ExporterField(parent=working_model, name=field, field=working_model.model._meta.get_field(field))
                        working_field.settings["join_only"] = True

            for model in app.get("models", []):
                working_model = ExporterModel(parent=working_app, name=model, model=apps.get_model(app_label=app['name'], model_name=model))

                # Add only fields that have columns in the db, and aren't in excluded fields
                log.debug(working_exporter.settings.get("exclude_fields", []) )
                for field in [field for field in working_model.model._meta.get_fields() if field.name not in working_exporter.settings.get("exclude_fields", []) and type(field) not in (ManyToOneRel, )]:
                    working_field = ExporterField(parent=working_model, name=field.name, field=field)