from django.conf import settings
from django.apps import apps
from django.db import models, connection
from django.core.exceptions import ImproperlyConfigured

import logging
log = logging.getLogger(settings.ML_EXPORT_WIZARD['Logger'])

from weakref import proxy
from collections import namedtuple

from ml_export_wizard.utils.simple import fancy_name, deep_exists
from ml_export_wizard.exceptions import MLExportWizardNoFieldFound


exporters: dict = {}


class BaseExporter(object):
    """ Base class to inherit from """

    def __init__(self, parent: object = None, name: str='', **settings) -> None:
        """ Initialise the object """

        if parent: self.parent = proxy(parent)  # Use a weakref so we don't have a circular refrence, defeating garbage collection
        self.name = name
        self.settings = {}
        
        for setting, value in settings.items():
            self.settings[setting] = value
            
    @property
    def fancy_name(self) -> str:
        return fancy_name(self.name)
    
    def __str__(self):
        """ Return the name attribute as __str__ """
        return f"{self.__class__}: {self.name}"
    

class Exporter(BaseExporter):
    """ Class to hold the exporters from settings.ML_EXPORT_WIZARD """

    def __init__(self, *, parent: object = None, name: str = '', type: str = '', description: str = '', long_name: str = '', **settings) -> None:
        """ Initalize the object """

        super().__init__(parent, name, **settings)

        self.long_name = long_name
        self.type = type
        self.apps = []
        self.apps_by_name = {}

    def base_sql(self, *, sql_only: bool=False, limit_before_join: dict=None, limit_after_join: dict=None) -> tuple:
        """ Returns a raw SQL query that would be used to generate the exporter data"""
        
        sql: str = ""
        sql_dict: dict[str: str] = {}

        for app in self.apps:
            sql_dict = merge_sql_dicts(sql_dict, app._sql_dict(limit_before_join=limit_before_join))

        if sql_dict.get("select"):
            sql += f"SELECT {sql_dict['select']} "

        if sql_dict.get("from"):
            sql += f"FROM {sql_dict['from']} "

        if sql_dict.get("where"):
            sql += f"WHERE {sql_dict['where']} "

        if sql_only:
            return sql % {key: f"'{value}'" for (key, value) in sql_dict["parameters"].items()}

        return (sql, sql_dict["parameters"])
    
    def query_count(self, *, count: any=None, group_by: dict|list|str=None, limit_before_join: dict=None, limit_after_join: dict=None) -> int:
        """ Build and execute a query to do a count, and return that count """

        sql_dict: dict = {}
        select_bit: str = ""
        returns: str = ""

        if group_by:
            returns = "value_dict"
        else:
            returns = "single_value"

        aggregate: dict = {
            "function": "count",
            "argument": count
        }

        return self._execute_query(sql_dict=sql_dict, group_by=group_by, returns=returns, limit_before_join=limit_before_join, limit_after_join=limit_after_join, aggregate=aggregate)

    def query_rows(self, *, count: any=None, group_by: dict|list|str=None, limit_before_join: dict=None, limit_after_join: dict=None, aggregate: dict|list=None) -> int:
        """ Build and execute a query to do a count, and return that count """

        returns: str = "list"

        return self._execute_query(group_by=group_by, returns=returns, limit_before_join=limit_before_join, limit_after_join=limit_after_join, aggregate=aggregate)

    def _execute_query(self, *, group_by: dict|list|str=None, limit_before_join: dict=None, limit_after_join: dict=None, sql_dict: dict=None, returns: str=None, aggregate: dict|list=None) -> object:
        """ Build the final query and execute it unless told not to 
            valid returns are: 
                single_value = value of the first column 
                value_dict = dict where the first column is the key, second column is the value"""

        if sql_dict: 
            sql_dict = sql_dict.copy()
        else:
            sql_dict = {}

        data: object = None

        # Set up Group By 
        if group_by:
            # If it's not a list stick it into a list so it can be processed the same
            if type(group_by) is not list:
                group_by = [group_by]
            
            for group in group_by:
                if type(group) is str:
                    field = self._get_field(field=group)
                else:
                    field = self._get_field(app=group.get("app"), model=group.get("model"), field=group.get("field"))

                sql_dict["group_by"] = ", ".join(filter(None, (sql_dict.get("group_by"), field.column)))
                sql_dict["select"] = ", ".join(filter(None, (field.column, sql_dict.get("select"))))

        # Set up Select
        if aggregate:
            # If it's not a list stick it inot a list so it can be processed the same
            if type(aggregate) is not list:
                aggregate = [aggregate]

            for column in aggregate:
                if column.get("function") == "count":
                    argument: str = column.get("argument", "*")
                    select_bit: str = ""

                    if not argument or argument == "*":
                        select_bit = "COUNT(*)"
                    elif argument.startswith("DISTINCT:"):
                        select_bit = f"COUNT(DISTINCT {argument.replace('DISTINCT:', '')})"
                    else:
                        select_bit = f"COUNT({argument})"

                    if "column_name" in column:
                        select_bit = f"{select_bit} AS {column['column_name']}"

                    sql_dict["select"] = ", ".join(filter(None, (sql_dict.get("select"), select_bit)))

        # Build the SQL
        sql, parameters = self.base_sql(limit_before_join=limit_before_join, limit_after_join=limit_after_join)
        sql = f"SELECT {sql_dict['select']} FROM ({sql}) AS {self.name}"

        if sql_dict.get("group_by"):
            sql = f"{sql} GROUP BY {sql_dict['group_by']}"

        # Do the actual query
        with connection.cursor() as cursor:
            cursor.execute(sql, parameters)

            columns = [col[0] for col in cursor.description]
            if returns == "single_value":
                return cursor.fetchone()[0]
            
            if returns == "value_dict":
                return {row[0]: row[1] for row in cursor.fetchall()}

            if returns == "list":
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return data

    def _get_field(self, app: str=None, model: str=None, field: str=None):
        """ Return a field object defined by app, model, field """

        if app and model and field:
            try: 
                app_object = self.apps_by_name[app]
                model_object = app_object.models_by_name[model]
                field_object = model_object.fields_by_name[field]
            except:
                raise MLExportWizardNoFieldFound(f"Field not found in exporter (exporter: {self.name}, app: {app}, model: {model}, field: {field})")
        
        elif field:
            fields: list[object] = []
            for app in self.apps:
                fields += app._get_field(field=field)

            if len(fields) == 0:
                raise MLExportWizardNoFieldFound(f"Field not found in exporter (exporter: {self.name}, field: {field})")
            elif len(fields) == 1:
                field_object = fields[0]
            else:
                raise MLExportWizardNoFieldFound(f"Field is ambiguous, try indicating the model or app (exporter: {self.name}, field: {field})")
            
        else:
            raise MLExportWizardNoFieldFound(f"Lookup for undefined field failed (exporter: {self.name})")

        return field_object

class ExporterApp(BaseExporter):
    """ Class to hold apps to export  """

    def __init__(self, *, parent: object = None, name: str='', **settings) -> None:
        """ Initialize the object """

        super().__init__(parent, name, **settings)
        
        self.models = []
        self.models_by_name = {}

        # List of models that have been used in the SQL.
        self.prepped_models = set()

        parent.apps.append(self)
        parent.apps_by_name[self.name] = self

    def _sql_dict(self, *, limit_before_join: dict = None, limit_after_join: dict = None) -> dict[str: str]:
        """ Create an SQL_Dict for the query bits from this app"""

        sql_dict: dict[str: str] = {}
        self.prepped_models = set()

        # Check that we have valid a primary model or throw a ImproperlyConfigured error
        if "primary_model" not in self.settings or not self.settings["primary_model"]:
            raise ImproperlyConfigured(f"No valid primary_model in Exporter: {self.parent.name}, App: {self.name}")
        
        sql_dict = self.models_by_name[self.settings["primary_model"]]._sql_dict(limit_before_join=limit_before_join)

        return sql_dict
    
    def _get_field(self, *, field: str=None) -> list:
        """ Gets a field from models in this app """
        fields: list = []

        for model in self.models:
            if field in model.fields_by_name:
                fields.append(model.fields_by_name[field])

        return fields


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

    def _sql_dict(self, *, table_name: str=None, left_join: bool=False, join_model: object=None, join_using: str=None, limit_before_join: dict=None, limit_after_join: dict=None) -> dict[str: str]:
        """ Create an SQL_Dict for the query bits from this model"""

        sql_dict: dict[str: str] = {}
        table: str = self.table

        # Enact limits that are supposed to happen before the tables are joined
        if limit_before_join and self.name in limit_before_join:
            where_bit: str = ""

            for field_name, value, operator in [(limit.get("field"), limit.get("value"), limit.get("operator", "=")) for limit in limit_before_join[self.name]]:
                field = self.fields_by_name[field_name]
                
                if operator == "=":
                    where_bit = "AND ".join(filter(None, (where_bit, f"{field.field.column}=%({field.field.column})s")))

                    if "parameters" not in sql_dict:
                        sql_dict["parameters"] = {}

                    sql_dict["parameters"][field.field.column] = value
            
            if where_bit:
                table = f" (SELECT * FROM {table} WHERE {where_bit}) AS {table}"

        join_criteria: str = ""

        if join_model:
            join_criteria = f"ON {self.table}.{join_using} = {join_model.table}.{join_using}"
        else:
            join_criteria = f"USING ({join_using})"

        if left_join:
            if join_using:
                sql_dict["from"] = f"LEFT JOIN {table} {join_criteria}"
        elif join_using:
            sql_dict["from"] = f"JOIN {table} {join_criteria}"
        else:
            sql_dict["from"] = table

        for field in self.fields:
            sql_dict = merge_sql_dicts(sql_dict, field._sql_dict(table_name=table_name))

        # Note that the model has been prepped
        self.parent.prepped_models.add(self)

        # Add models that this model joins with
        for field in self.fields:
            field_object = field.field

            if type(field_object) in (models.ManyToOneRel, models.ForeignKey, models.OneToOneRel) and field_object.related_model.__name__ in self.parent.models_by_name:
                join_model = self.parent.models_by_name[field_object.related_model.__name__]
                
                # don't link to the model if it is in this models dont_link_to, or this model is in its dont_link_to
                if join_model in self.parent.prepped_models or \
                    ("dont_link_to" in self.settings and join_model.name in self.settings["dont_link_to"] or \
                    "dont_link_to" in join_model.settings and self.name in join_model.settings["dont_link_to"]):
                    
                    continue

                # Currently making all joins left joins.  Not sure how to handle this.
                sql_dict = merge_sql_dicts(sql_dict, join_model._sql_dict(left_join=True, join_model=self, join_using=field.column, limit_before_join=limit_before_join))
               
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

        if hasattr(self.field, "column"):
            return self.field.column
        
        if hasattr(self.field, "field_name"):
            return self.field.field_name

    def is_foreign_key(self) -> bool:
        """ returns True if the field has a foreign key """

        return isinstance(self.field, models.ForeignKey)
    
    def _sql_dict(self, *, table_name: str = None) -> dict[str: str]:
        """ Create an SQL_Dict for the query bits from this field"""

        if self.settings.get("join_only") or type(self.field) in (models.ManyToOneRel, models.ManyToManyField, models.ManyToManyRel, models.OneToOneRel,): #models.OneToOneRel, 
            return {}
        
        sql_dict: dict[str: str] = {}
        column: str = ""

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
                               "from": " ",
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

    if "parameters" not in dict1 and "parameters" not in dict2:
        merged["parameters"] = {}
    elif "parameters" in dict1 and "parameters" not in dict2:
        merged["parameters"] = dict1["parameters"]
    elif "parameters" in dict2 and "parameters" not in dict1:
        merged["parameters"] = dict2["parameters"]
    else:
        merged["parameters"] = dict1["parameters"] | dict2["parameters"]

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

            # for pseudomodel in app.get("pseudomodels", []):
            #     # Get settingsfor the pseudomodel
            #     exclude_keys: tuple = ("name", "models")
            #     pseudomodel_settings = {setting: value for setting, value in pseudomodel.items() if setting not in exclude_keys}

            #     working_pseudomodel = ExporterPseudomodel(parent=working_app, name=pseudomodel.get("name", ""), **pseudomodel_settings)

            #     for model in pseudomodel.get("models", []):
            #         # Get settings for the model
            #         exclude_keys: tuple = ("name", "fields")
            #         model_settings = {setting: value for setting, value in model.items() if setting not in exclude_keys}

            #         working_model = ExporterModel(parent=working_pseudomodel, name=model.get("name", ""), model=apps.get_model(app_label=app['name'], model_name=model.get("name", "")), **model_settings)

            #         for field in model.get("fields", []):
            #             working_field = ExporterField(parent=working_model, name=field, field=working_model.model._meta.get_field(field))

            #         for field in model.get("join_only_fields", []):
            #             working_field = ExporterField(parent=working_model, name=field, field=working_model.model._meta.get_field(field))
            #             working_field.settings["join_only"] = True

            models: list = []

            # Get models from include_models if it exists
            if "include_models" in app:
                models = [apps.get_model(app_label=app["name"], model_name=model) for model in app["include_models"]]
            
            # Get models from app if we don't have models yet
            if not models:
                models = [model for model in apps.get_app_config(app['name']).get_models() if model.__name__ not in app.get("exclude_models", [])]

            for model in models:
                model_settings: dict = {}

                if deep_exists(app, ["models", model.__name__]):
                    model_settings = app["models"][model.__name__]

                working_model = ExporterModel(parent=working_app, name=model.__name__, model=model, **model_settings)

                # Add only fields that have columns in the db, and aren't in excluded fields
                for field in [field for field in working_model.model._meta.get_fields() if field.name not in working_exporter.settings.get("exclude_fields", [])]:
                    working_field = ExporterField(parent=working_model, name=field.name, field=field)