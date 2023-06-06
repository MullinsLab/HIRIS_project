import copy
from weakref import proxy
from collections import namedtuple

from django.conf import settings
from django.apps import apps
from django.db import models, connection
from django.core.exceptions import ImproperlyConfigured

import logging
log = logging.getLogger(settings.ML_EXPORT_WIZARD['Logger'])

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
    
    def __str__(self):
        """ Return the name attribute as __str__ """
        return f"{self.__class__}: {self.name}"
            
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
        self.rollups = []
        self.rollups_by_name = {}

    def base_sql(self, *, sql_only: bool=False, where_before_join: dict=None, where: dict=None, query_layer: str=None) -> tuple|str:
        """ Returns a raw SQL query that would be used to generate the exporter data"""
        
        sql: str = ""
        sql_dict: dict[str: str] = {}

        if query_layer == "inner":
            rollup_query_layer="middle"
        else:
            rollup_query_layer = "outer"

        for app in self.apps:
            sql_dict = merge_sql_dicts(sql_dict, app._sql_dict(where_before_join=where_before_join, query_layer=query_layer))

        for rollup in self.rollups:
            sql_dict = merge_sql_dicts(sql_dict, rollup._sql_dict(where_before_join=where_before_join, query_layer=rollup_query_layer))

        if sql_dict.get("select"):
            sql += f"SELECT {sql_dict['select']} "

        if sql_dict.get("from"):
            sql += f"FROM {sql_dict['from']} "

        if sql_dict.get("where"):
            sql += f"WHERE {sql_dict['where']} "

        if sql_only:
            return sql % {key: f"'{value}'" for (key, value) in sql_dict.get("parameters", {}).items()}

        return (sql, sql_dict["parameters"])
    
    def query_count(self, *, count: any=None, group_by: dict|list|str=None, where_before_join: dict=None, where: dict=None) -> int:
        """ Build and execute a query to do a count, and return that count """

        sql_dict: dict = {}
        select_bit: str = ""
        returns: str = ""

        if group_by:
            returns = "value_dict"
        else:
            returns = "single_value"

        if count and count.startswith("DISTINCT:"):
            extra_field: dict = {
                "function": "count",
                "source_field": count.replace('DISTINCT:', ''),
                "distinct": True,
            }
        else:
            extra_field: dict = {
                "function": "count",
                "source_field": count
            }

        return self.execute_query(sql_dict=sql_dict, group_by=group_by, returns=returns, where_before_join=where_before_join, where=where, extra_field=extra_field)

    def query_rows(self, *, count: any=None, group_by: dict|list|str=None, where_before_join: dict=None, where: dict=None, extra_field: dict|list=None, order_by: str|list=None, limit: int=None) -> list:
        """ Build and execute a query to do a count, and return that count """

        returns: str = "list"

        return self.execute_query(group_by=group_by, returns=returns, where_before_join=where_before_join, where=where, extra_field=extra_field, order_by=order_by, limit=limit)

    def get_field(self, app: str=None, model: str=None, field: str=None):
        """ Return a field object defined by app, model, field """

        # See if the field is in app.model.field format
        if field and not app and not model and field.count(".") == 2:
            app, model, field = field.split(".")

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

            for rollup in self.rollups:
                fields += rollup._get_field(field=field)

            if len(fields) == 0:
                raise MLExportWizardNoFieldFound(f"Field not found in exporter (exporter: {self.name}, field: {field})")
            elif len(fields) == 1:
                field_object = fields[0]
            else:
                raise MLExportWizardNoFieldFound(f"Field is ambiguous, try indicating the model or app (exporter: {self.name}, field: {field})")
            
        else:
            raise MLExportWizardNoFieldFound(f"Lookup for undefined field failed (exporter: {self.name})")

        return field_object
    
    def execute_query(self, *args, returns: str=None, **kwargs) -> any:
        """ execute the final query
            valid returns are: 
                single_value = value of the first column 
                value_dict = dict where the first column is the key, second column is the value
                list = list of rows containg key/value dict of the fields """

        sql, parameters = self.final_sql(**kwargs)

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

    def final_sql(self, *, sql_dict: dict=None, where_before_join: dict=None, where: dict=None, group_by: dict|list|str=None, order_by: str|list=None, limit: int=None, extra_field: dict|list=None, query_layer: str=None) -> tuple[str, dict]:
        """ Build the final query """

        parameters: dict = {}

        if query_layer == "inner":
            field_query_layer = "middle"
        else:
            field_query_layer = None

        if sql_dict: 
            sql_dict = sql_dict.copy()
        else:
            sql_dict = {}

        # Set up Select
        if extra_field:
            # If it's not a list stick it into a list so it can be processed the same
            if type(extra_field) is not list:
                extra_field = [extra_field]

            for column in extra_field:
                (added_select_bit, added_parameters) = self._resolve_extra_field(column=column, query_layer=query_layer, field_query_layer=field_query_layer)
                sql_dict["select"] = ", ".join(filter(None, (sql_dict.get("select"), added_select_bit)))
                parameters = parameters | added_parameters

        # Set up Group By 
        if group_by:
            # If it's not a list stick it into a list so it can be processed the same
            if type(group_by) is not list:
                group_by = [group_by]
            
            for group in group_by:
                if type(group) is str:
                    field = self.get_field(field=group)
                else:
                    field = self.get_field(app=group.get("app"), model=group.get("model"), field=group.get("field"))

                sql_dict["group_by"] = ", ".join(filter(None, (sql_dict.get("group_by"), field.column(query_layer=field_query_layer))))
                sql_dict["select"] = ", ".join(filter(None, (field.column(query_layer=field_query_layer), sql_dict.get("select"))))

        # Set up Order By
        if order_by:
            if type(order_by) is not list:
                order_by = [order_by]

            for order_set in order_by:
                order: str = "ASC"
                order_field: str = None
                field: ExporterField = None

                if type(order_set) is str:
                    order_field = order_set
                    
                else:
                    if field in order_set:
                        order_field = order_set["field"]
                    else:
                        order_field = order_set

                    if "order" in order_set:
                        order = order_set["order"]

                if type(order_field) is str:
                    field = self.get_field(field=order_field);
                else:
                    field = self.get_field(app=order_field.get("app"), model=order_field.get("model"), field=order_field.get("field"))

                order_bit = f"{field.column(query_layer=field_query_layer)} {order}"

                sql_dict["order_by"] = ", ".join(filter(None, (sql_dict.get("order_by"), order_bit)))

        if limit:
            sql_dict["limit"] = limit

        if where:
            if type(where) is not list:
                where = [where]

            for where_item in where:
                added_parameters: dict = {}

                if type(where_item["field"]) is str:
                    field = self.get_field(field=where_item["field"])
                else:
                    field = self.get_field(app=where_item["field"].get("app"), model=where_item["field"].get("model"), field=where_item["field"].get("field"))

                if "value" in where_item:
                    if "operator" in where_item:
                        operator = where_item["operator"]
                    else:
                        operator = "="

                    where_bit = f"{field.column(query_layer=field_query_layer)} {operator} %({field.column(query_layer=field_query_layer)})s"
                    added_parameters[field.column(query_layer=field_query_layer)] = where_item["value"]

                elif "not_null" in where_item:
                    where_bit = f"{field.column(query_layer=field_query_layer)} IS NOT NULL"

                sql_dict["where"] = " AND ".join(filter(None, (sql_dict.get("where"), where_bit)))                        
                parameters = parameters | added_parameters

        # Build the SQL
        sql, added_parameters = self.base_sql(where_before_join=where_before_join, where=where, query_layer=query_layer)
        parameters = parameters | added_parameters

        if sql_dict.get("select"):
            sql = f"SELECT {sql_dict['select']} FROM ({sql}) AS {self.name}"
        else:
            sql = f"SELECT * FROM ({sql}) AS {self.name}"

        if sql_dict.get("group_by"):
            sql = f"{sql} GROUP BY {sql_dict['group_by']}"

        if sql_dict.get("where"):
            sql = f"{sql} WHERE {sql_dict['where']}"

        if sql_dict.get("order_by"):
            sql = f"{sql} ORDER BY {sql_dict['order_by']}"

        if sql_dict.get("limit"):
            sql = f"{sql} LIMIT {sql_dict['limit']}"

        return (sql, parameters)
    
    def _resolve_extra_field(self, *, column: dict=None, query_layer: str=None, field_query_layer: str=None) -> tuple[str, dict]:
        """ Resolve the aggragates to sql statements.  Returns an SQL string, and a dictionary of parameters """

        if "value" in column:
            if column["value"] is None:
                return ("Null", [])

        field: object = None
        select_bit: str = ""
        parameters: dict = {}
        field_column: str = ""
        fields: list = []

        # Get the field object to work with
        if column.get("source_field"):
            if type(column["source_field"]) is not list:
                source_fields = [column["source_field"]]
            else:
                source_fields = column["source_field"]

            for source_field in source_fields:
                if type(source_field) is str:

                    # If source_field in app.model.field format
                    if source_field.count(".") == 2:
                        app, model, field = source_field.split(".")
                        fields.append(self.get_field(app=app, model=model, field=field))

                    elif source_field and source_field != "*":
                        fields.append(self.get_field(field=source_field))

                elif type(source_field) is dict:
                    fields.append(self.get_field(app=column.get("app"), model=column.get("model"), field=column.get("field")))

            # Resolve the select bit for the agragate
            if len(fields) == 1:
                field_column = fields[0].column(query_layer=field_query_layer)
            
            elif len(fields) > 1:
                for field in fields:
                    field_column = ", ".join(filter(None, (field_column, field.column(query_layer=field_query_layer))))

                field_column = f"ROW({field_column})"
        else:
            field_column = None

        match column.get("function"):
            case "sum":
                if field_column:
                    select_bit = f"SUM({field_column})"

            case "count":
                if field_column:
                    select_bit = f"COUNT({'DISTINCT ' if column.get('distinct') else ''}{field_column})"
                else:
                    select_bit = "COUNT(*)"

            case "case":
                if field_column:
                    select_bit = f"CASE {field_column}"
                
                if type(column.get("when")) is dict:
                    column["when"] = [column["when"]]

                for when in column.get("when", []):
                    if when.get("condition"):
                        (added_select_bit, added_parameters) = self._resolve_extra_field(column=when['extra_field'], field_query_layer=field_query_layer)
                        select_bit = f"{select_bit} WHEN %({column['column_name']}_{column['when'].index(when)})s THEN {added_select_bit}"

                        parameters[f"{column['column_name']}_{column['when'].index(when)}"] = when["condition"]
                        parameters = parameters | added_parameters

                    elif when.get("else"):
                        (added_select_bit, added_parameters) = self._resolve_extra_field(column=when['extra_field'], field_query_layer=field_query_layer)

                        select_bit = f"{select_bit} ELSE {added_select_bit}"
                        parameters = parameters | added_parameters

                select_bit = f"{select_bit} END"

        if column.get("cast"):
            select_bit = f"{select_bit}::{column['cast']}"

        if column.get("filter"):
            if type (column["filter"]) is not list:
                column["filter"] = [column["filter"]]

            where_bit: str = ""

            for filter_item in column.get("filter", []):
                field = self.get_field(field=filter_item["field"])
                where_bit, added_parameters = _resolve_where(operator=filter_item["operator"], value=filter_item["value"], field=field, query_layer=field_query_layer)

            if where_bit:
                select_bit = f"{select_bit} FILTER (WHERE {where_bit})"
                parameters = parameters | added_parameters

        if column.get("column_name"):
            # if field_query_layer != 'outer':
            #     select_bit = f"{select_bit} AS {self.name}_{column['column_name']}"
            # else:
            #     select_bit = f"{select_bit} AS {column['column_name']}"
            select_bit = f"{select_bit} AS {column['column_name']}"

        return (select_bit, parameters)


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

    def _sql_dict(self, *, where_before_join: dict=None, where: dict=None, query_layer: str=None) -> dict[str: str]:
        """ Create an SQL_Dict for the query bits from this app"""

        sql_dict: dict[str: str] = {}
        self.prepped_models = set()

        # Check that we have valid a primary model or throw a ImproperlyConfigured error
        if "primary_model" not in self.settings or not self.settings["primary_model"]:
            raise ImproperlyConfigured(f"No valid primary_model in Exporter: {self.parent.name}, App: {self.name}")
        
        sql_dict = self.models_by_name[self.settings["primary_model"]]._sql_dict(where_before_join=where_before_join, query_layer=query_layer)

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

    def _sql_dict(self, *, table_name: str=None, left_join: bool=False, join_model: object=None, join_using: str=None, where_before_join: dict=None, where: dict=None, query_layer: str=None) -> dict[str: str]:
        """ Create an SQL_Dict for the query bits from this model"""

        sql_dict: dict[str: str] = {}
        table: str = self.table

        # Enact limits that are supposed to happen before the tables are joined
        if where_before_join and self.name in where_before_join:
            where_bit: str = ""

            for field_name, value, operator in [(limit.get("field"), limit.get("value"), limit.get("operator", "=")) for limit in where_before_join[self.name]]:
                field = self.fields_by_name[field_name]
                
                where_bit, parameters = _resolve_where(field=field, operator=operator, value=value)
                sql_dict["parameters"] = sql_dict.get("parameters", {}) | parameters
            
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
            sql_dict = merge_sql_dicts(sql_dict, field._sql_dict(table_name=table_name, query_layer=query_layer))

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
                sql_dict = merge_sql_dicts(sql_dict, join_model._sql_dict(left_join=True, join_model=self, join_using=field.column(), where_before_join=where_before_join, query_layer=query_layer))
               
        return sql_dict


class ExporterRollup(BaseExporter):
    """ Class to hold exporters that use other exporters as models """

    def __init__(self, *, parent: object=None, name: str="", exporter: str=None, **settings) -> None:
        """ Initialise the object"""

        super().__init__(parent, name, **settings)

        self.exporter = exporters[exporter]

        parent.rollups.append(self)
        parent.rollups_by_name[self.name] = self

        self.fields = []
        self.fields_by_name = {}

        # Add the fields used to this rollup to generate selects, etc.
        for field in self.settings.get("group_by", []):
            if "." in field:
                app, model, field = field.split(".")
                field_object = self.exporter.get_field(app=app, model=model, field=field)
            else:
                field_object = self.exporter.get_field(field=field)

            self.fields.append(field_object)
            self.fields_by_name[field_object.name] = field_object

        # Add psudofields for agragates so field names can be looked up
        for extra_field in self.settings.get("extra_field", []):
            pseudofield = ExporterPseudofield(parent=self, name=extra_field["column_name"])

            self.fields.append(pseudofield)
            self.fields_by_name[pseudofield.name] = pseudofield

    @property
    def table(self) -> str:
        """ returns the db table name to query against """

        return self.name
    
    def _sql_dict(self, *, where_before_join: dict=None, where: dict=None, query_layer: str=None) -> tuple|str:
        """ Returns a raw SQL query that would be used to generate the exporter data"""

        sql_dict: dict = {}

        if not where_before_join and "where_before_join" in self.settings:
            where_before_join = self.settings["where_before_join"]

        elif where_before_join and "where_before_join" in self.settings:
            where_before_join = where_before_join | self.settings["where_before_join"]

        from_bit, sql_dict["parameters"] = self.exporter.final_sql(where_before_join=where_before_join, where=where, group_by=self.settings.get("group_by"), extra_field=self.settings.get("extra_field"), query_layer="inner")
        
        sql_dict["from"] = f"({from_bit}) AS {self.name}"

        for field in self.fields:
            sql_dict = merge_sql_dicts(sql_dict, field._sql_dict(table_name=self.name, query_layer=query_layer))

        for aggragate in self.settings.get("extra_field", []):
            sql_dict["select"] = ", ".join(filter(None, (sql_dict["select"], aggragate['column_name'])))

        return sql_dict
    
    def _get_field(self, *, field: str=None) -> list:
        """ Gets a field from this rollup """
        fields: list = []

        if field in self.fields_by_name:
            fields.append(self.fields_by_name[field])

        return fields


class ExporterField(BaseExporter):
    """ Class to hold the fields to export """

    def __init__(self, *, parent: object = None, name: str="", field: object = None, **settings) -> None:
        """ Initialise the object"""

        super().__init__(parent, name, **settings)

        self.field = field

        parent.fields.append(self)
        parent.fields_by_name[self.name] = self

    def column(self, *, query_layer: str=None) -> str:
        """ returns the name of the DB column for the field"""

        column: str = ""

        if hasattr(self.field, "column"):
            column = self.field.column
        elif hasattr(self.field, "field_name"):
            column = self.field.field_name
        
        if query_layer == "inner":
            column = f"{column} AS {self.parent.table}_{column}"
        elif query_layer=="middle":
            column = f"{self.parent.table}_{column}"
        elif query_layer == "outer":
            column = f"{self.parent.table}_{column} as {column}"

        return column

    @property
    def is_text(self) -> bool:
        """ True if the field holds text, False if it doesn't """

        if type(self.field) in (models.CharField, models.TextChoices, models.TextField):
            return True
    
        return False
    
    @property
    def is_foreign_key(self) -> bool:
        """ returns True if the field has a foreign key """

        return isinstance(self.field, models.ForeignKey)
    
    def _sql_dict(self, *, table_name: str=None, query_layer: str=None) -> dict[str: str]:
        """ Create an SQL_Dict for the query bits from this field"""

        # Don't include this field in the select if it's there just for joining, or if it is a reference to a different table
        if self.settings.get("join_only") or type(self.field) in (models.ManyToOneRel, models.ManyToManyField, models.ManyToManyRel, models.OneToOneRel, models.ForeignKey): #models.OneToOneRel, 
            return {}
        
        sql_dict: dict[str: str] = {}

        if table_name:
            sql_dict["select"] = f"{table_name}.{self.column(query_layer=query_layer)}"
        else:
            sql_dict["select"] = f"{self.parent.table}.{self.column(query_layer=query_layer)}"

        sql_dict["select_no_table"] = self.column(query_layer=query_layer)

        return sql_dict
    

class ExporterPseudofield(BaseExporter):
    """ Holds information on field like objects used to get field names """

    def __init__(self, *, parent: object = None, name: str="", **settings) -> None:
        """ Initialise the object"""

        super().__init__(parent, name, **settings)

        parent.fields.append(self)
        parent.fields_by_name[self.name] = self

    def column(self, *, query_layer: str=None) -> str:
        """ returns the name of the DB column for the pseudofield """

        column: str = self.name

        return column

    def _sql_dict(self, *, table_name: str=None, query_layer: str=None) -> dict[str: str]:
        """ Reuturns a blank sql_dict """
        
        sql_dict: dict[str: str] = {}

        return sql_dict


def _resolve_where(*, operator: str=None, field: ExporterField|ExporterPseudofield=None, value: str|int|float=None, query_layer: str=None) -> tuple[str, dict]:
    """ Resolve the where bit of a query. Returns a tuple with the where part and parameters """

    if not operator or not field or not value:
        return (None, None)

    where_bit: str = ""
    parameters: dict = {}
    field_column = field.column(query_layer=query_layer)

    if operator in ("=", ">=", "<=", "<>", "!="):
        where_bit = "AND ".join(filter(None, (where_bit, f"{field_column}{operator}%({field_column})s")))

    parameters[field_column] = value

    return (where_bit, parameters)


def merge_sql_dicts(dict1: dict = None, dict2: dict = None) -> dict[str: any]:
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

    for exporter in settings.ML_EXPORT_WIZARD["Exporters"]:
        exclude_keys: tuple = ("name", "description", "apps", "exporter")
        exporter_settings = {setting: value for setting, value in exporter.items() if setting not in exclude_keys}
        working_exporter = exporters[exporter["name"]] = Exporter(name = exporter["name"], long_name = exporter.get('long_name', ''), description = exporter.get('description', ''), **exporter_settings)

        for app in exporter.get("apps", []):
            # Get settings for the app and save them in the object, except keys in exclude_keys
            exclude_keys: tuple = ("name", "models", "psudomodels")
            app_settings = {setting: value for setting, value in app.items() if setting not in exclude_keys}
            working_app: ExporterApp = ExporterApp(parent=working_exporter, name=app.get('name', ''), **app_settings)

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
        
        for rollup in exporter.get("rollups", []):
            exclude_keys: tuple = ("name", "exporter")
            rollup_settings = {setting: value for setting, value in rollup.items() if setting not in exclude_keys}
            working_rollup: ExporterRollup = ExporterRollup(parent=working_exporter, name=rollup.get('name'), exporter=rollup.get("exporter"), **rollup_settings)