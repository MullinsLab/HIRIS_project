from django.conf import settings
from django.db import models, IntegrityError, transaction
from django.db.models.functions import Lower

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from pathlib import Path
from itertools import islice
import subprocess, csv, inspect, os.path, sqlite3

# Check to see if gffutils is installed
NO_GFFUTILS: bool = False
from importlib.util import find_spec
if (find_spec("gffutils")): import gffutils 
else: NO_GFFUTILS=True

from ml_import_wizard.utils.simple import dict_hash, stringalize, fancy_name, deep_exists
from ml_import_wizard.exceptions import GFFUtilsNotInstalledError, FileNotReadyError, ImportSchemeNotReady, StatusNotFound
from ml_import_wizard.utils.importer import importers
from ml_import_wizard.decorators import timeit
from ml_import_wizard.utils.cache import LRUCacheThing


class ImportBaseModel(models.Model):
    ''' A base class to hold comon methods and attributes.  It's Abstract so Django won't make a table for it
    The # pragma: no cover keeps the lines from being counted in coverage percentages '''

    id = models.BigAutoField(primary_key=True, editable=False)

    class Meta:
        abstract = True
    
    def __str__(self) -> str:
        ''' Generic stringify function.  Most objects will have a name so it's the default. '''
        return self.name                    # type: ignore   # pragma: no cover
    
    def set_with_dirty(self, field: str, value: any) -> bool:
        """ Sets a value if it's changed, and returns True for dirty, or False for clean """

        if getattr(self, field) != value:
            setattr(self, field, value)
            return True
        
        return False
    

class ImportSchemeStatus(ImportBaseModel):
    """ Holds statuses for ImportScheme objects """

    name = models.CharField(max_length=255)
    files_received = models.BooleanField(default=False)
    files_inspected = models.BooleanField(default=False)
    data_previewed = models.BooleanField(default=False)
    import_defined = models.BooleanField(default=False)
    import_started = models.BooleanField(default=False)
    import_completed = models.BooleanField(default=False)


class ImportScheme(ImportBaseModel):
    '''  Import scheme holds all required information to import a specific file format. FIELDS:(name, importer, user) '''
    
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    importer = models.CharField(max_length=255, null=False, blank=False, editable=False)
    importer_hash = models.CharField(max_length=32, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.ForeignKey(ImportSchemeStatus, on_delete=models.DO_NOTHING, default=1, related_name="schemes")
    public = models.BooleanField(default=True)
    settings = models.JSONField(null=False, blank=False, default=dict)

    def save(self, *args, **kwargs) -> None:
        ''' Override Save to store the importer_hash.  This is used to know if the Importer definition has changed, invalidating this importer  '''

        if not self.importer_hash:
            self.importer_hash = dict_hash(settings.ML_IMPORT_WIZARD['Importers'][self.importer])
        
        if self.status == None:
            self.status = {}

        super().save(*args, **kwargs)

    @property
    def files_linked(self) -> bool:
        """ Reuturns a bool indicating whether the files are adaqately linked to result in a single row of data while importing"""

        if self.files.count()>=2 and not self.settings.get("file_links", None):
            return False
        
        return True

    def set_status_by_name(self, status):
        """ Looks up the status name and """

        try:
            status_object = ImportSchemeStatus.objects.get(name=status)
        except ImportSchemeStatus.DoesNotExist:
            raise StatusNotFound(f"ImportSchemeStatus {status} is not valid")
        
        self.status = status_object

    def files_min_status_settings(self) -> dict[str: bool]:
        """ Returns the minimum status settings of the files for this scheme """

        statuses: dict[str: bool] = {}
        for file in self.files.all():
            for field in ImportSchemeFileStatus._meta.get_fields():
                if field.get_internal_type() == "BooleanField":
                    if not getattr(file.status, field.name):
                        statuses[field.name] = False
                    elif field.name not in statuses:
                            statuses[field.name] = True

        return statuses


    def list_files(self, *, separator: str = ", ") -> str:
        """ Return a string that contains a list of file names for this ImportScheme """
        file_list: list[str] = []
        
        for file in self.files.all():
            file_list.append(file.name)

        return separator.join(file_list)
    
    def create_or_update_item(self, *, app: str, model: str, field: str, strategy: str, settings: dict) -> ImportBaseModel:
        """ Create or update an ImportSchemeItem.  Keys by app, model, and field """

        dirty: bool = False

        items = self.items.filter(app=app, model=model, field=field)
        if items.count() == 0:
            item = self.items.create(app=app, model=model, field=field)
            dirty = True
        else:
            item = items[0]

        if item.set_with_dirty("strategy", strategy):
            dirty = True

        if item.set_with_dirty("settings", settings):
            dirty = True

        if dirty: item.save()

        return item
    
    def preview_data_table(self, limit_count: int=100) -> dict:
        """ Get preview data for showing to the user """
        
        if self.status.import_defined == False:
            raise ImportSchemeNotReady(f"Import scheme {self.name} ({self.id}) has not been set up.")

        table: dict = {"columns": self.data_columns(),
                       "rows": []            
        }

        for row in self.data_rows(columns = table["columns"], limit_count=limit_count):
            table["rows"].append(row)

        return table

    def data_columns(self) -> list[dict[str: any]]:
        """ Returns a list of columns for each set of models in the target importer """
        columns: list = []
        column_id: int = 0
        importer = importers[self.importer]

        for app in importer.apps:
            for model in app.models:
                for field in model.fields:
                    try:
                        import_scheme_item = ImportSchemeItem.objects.get(import_scheme_id = self.id,
                                                                          app = app.name,
                                                                          model = model.name,
                                                                          field = field.name
                        )
                    except ImportSchemeItem.DoesNotExist:
                        continue

                    columns.append({})
                    columns[column_id]["name"] = field.name
                    columns[column_id]["import_scheme_item"] = import_scheme_item
                    columns[column_id]["importer_field"] = field
                    columns[column_id]["importer_model"] = model

                    column_id += 1
        return columns
    
    def data_rows(self, *, columns: list = None, limit_count: int = None) -> dict[str: any]:
        """ Yields a row for each set of models in the target importer """

        # Fields holds a list of ImportSchemeItem.ids and the associated ImportSchemeFile.id and ImportSchemeFileField names
        fields: dict[int: dict] = {}

        if columns is None:
            columns = self.data_columns

        primary_file: ImportSchemeFile = None
        child_files: dict[int: dict] = {}

        # Set up information about the files that are not primary (child files)
        if self.files.count() > 1:
            primary_file = self.files.get(pk=int(self.settings["primary_file_id"]))
            for file, value in self.settings["file_links"].items():
                child = child_files[int(file)] = {}
                
                child["cache"] = LRUCacheThing(items=100000)
                child["object"] = self.files.get(pk=int(file))

                # Create a db connection to use for loading data if the file has a db
                child["connection"] = child["object"]._get_db_connection()

                # Store the child and primary linked fields that the child row will be looked up by
                import_scheme_file_field = ImportSchemeFileField.objects.get(pk=value["child"])
                fields[import_scheme_file_field.id] = {
                    "name": import_scheme_file_field.name,
                    "file": import_scheme_file_field.import_scheme_file_id,
                }
                child["child_linked_field"] = import_scheme_file_field.name

                import_scheme_file_field = ImportSchemeFileField.objects.get(pk=value["primary"])
                fields[import_scheme_file_field.id] = {
                    "name": import_scheme_file_field.name,
                    "file": import_scheme_file_field.import_scheme_file_id,
                }
                child["primary_linked_field"] = import_scheme_file_field.name
        else:
            primary_file = self.files.all()[0]

        for row in primary_file.rows(limit_count=limit_count):
            row_dict: dict = {"***row***setting***": {}}

            for column in columns:
                strategy = column["import_scheme_item"].strategy
                settings = column["import_scheme_item"].settings

                # Raw Text
                if strategy == "Raw Text":
                    row_dict[column["name"]] = settings["raw_text"]

                # Table Row - A value loaded from a table
                elif strategy == "Table Row":
                    row_dict[column["name"]] = settings["row"]

                # No Data
                elif strategy == "No Data":
                    row_dict[column["name"]] = None

                # File field - The 'regular' import of a field directly from the file
                elif strategy == "File Field":
                    key = settings["key"]

                    if key not in fields:
                        import_scheme_file_field = ImportSchemeFileField.objects.get(pk=key)
                        fields[import_scheme_file_field.id] = {
                            "name": import_scheme_file_field.name,
                            "file": import_scheme_file_field.import_scheme_file_id,
                        }

                    file = fields[key]["file"]
                    
                    if file == primary_file.id:
                        if type(row) is dict:
                            row_dict[column["name"]] = row.get(fields[key]["name"])
                        else:
                            row_dict[column["name"]] = row[fields[key]["name"]]
                    else:
                        child_row = child_files[file]["object"].find_row_by_key(
                            field=child_files[file]["child_linked_field"],
                            key=row.get(child_files[file]["primary_linked_field"]),
                            connection=child_files[file]["connection"],
                            #cache=child_files[file]["cache"],
                        )
                        if child_row:
                            if type(child_row) is dict:
                                row_dict[column["name"]] = child_row.get(fields[key]["name"])
                            else:
                                row_dict[column["name"]] = child_row[fields[key]["name"]]
                
                # Select first field
                elif strategy == "Select First":
                    value: str = None

                    for key in settings.get("first_keys", []):
                        if key not in fields:
                            import_scheme_file_field = ImportSchemeFileField.objects.get(pk=key)
                            fields[import_scheme_file_field.id] = {
                                "name": import_scheme_file_field.name,
                                "file": import_scheme_file_field.import_scheme_file_id,
                            }

                        file = fields[key]["file"]

                        if file == primary_file.id:
                            value = row.get(fields[key]["name"], None)
                        else:
                            child_row = child_files[file]["object"].find_row_by_key(
                                field=child_files[file]["child_linked_field"],
                                key=row[child_files[file]["primary_linked_field"]],
                                connection=child_files[file]["connection"],
                                #cache=child_files[file]["cache"],
                            )
                            if child_row:
                                value = child_row[fields[key]["name"]]

                        if value:
                            break
                    
                    row_dict[column["name"]] = value

                # Split field
                elif strategy == "Split Field":
                    key = settings["split_key"]

                    if key not in fields:
                        import_scheme_file_field = ImportSchemeFileField.objects.get(pk=key)
                        fields[import_scheme_file_field.id] = {
                            "name": import_scheme_file_field.name,
                            "file": import_scheme_file_field.import_scheme_file_id,
                        }
                    
                    value: str
                    file = fields[key]["file"]

                    if file == primary_file.id:
                        value = row.get(fields[key]["name"], None)
                    else:
                        child_row = child_files[file]["object"].find_row_by_key(
                            field=child_files[file]["child_linked_field"],
                            key=row[child_files[file]["primary_linked_field"]],
                            connection=child_files[file]["connection"],
                            #cache=child_files[file]["cache"],
                        )
                        if child_row:
                            value = child_row[fields[key]["name"]]
                    
                    if settings["splitter"] in value:
                        row_dict[column["name"]] = value.split(settings["splitter"])[settings["splitter_position"]-1]
                    else:
                        row_dict[column["name"]] = value

                # Adjust data
                if column["name"] in row_dict:
                    # Change "null" to none
                    if type(row_dict[column["name"]]) is str and row_dict[column["name"]].lower() == "null":
                        row_dict[column["name"]] = None

                    # Translate value in field
                    if "translate_values" in column["importer_model"].settings:
                        if row_dict[column["name"]] in column["importer_model"].settings["translate_values"]:
                            row_dict[column["name"]] = column["importer_model"].settings["translate_values"][row_dict[column["name"]]]

                    # Change case of value in field
                    if column["importer_field"].settings.get("force_case", "") == "upper":
                        row_dict[column["name"]] = row_dict[column["name"]].upper()

                    if column["importer_field"].settings.get("force_case", "") == "lower":
                        row_dict[column["name"]] = row_dict[column["name"]].lower()

                # Check the data for rejections and store that in row_dict[***row***setting***][reject_row]
                if column["importer_model"].settings.get("restriction", "") == "rejected":
                    if "approved_values" in column["importer_field"].settings:
                        if row_dict[column["name"]] not in column["importer_field"].settings.get("approved_values", []):
                            if "reject_row" not in row_dict["***row***setting***"]:
                                row_dict["***row***setting***"]["reject_row"] = []
                            
                            row_dict["***row***setting***"]["reject_row"].append({column['name']: row_dict[column['name']]})

            yield row_dict

    @timeit
    def execute(self, *, ignore_status: bool = False, limit_count: int=None) -> None:
        """ Execute the actual import and store the data """

        if not ignore_status and self.status.import_defined == False:
            raise ImportSchemeNotReady(f"Import scheme {self.name} ({self.id}) has not been set up.")
        
        if not ignore_status and self.status.import_completed == True:
            raise ImportSchemeNotReady(f"Import scheme {self.name} ({self.id}) has already been imported.")
        
        cache_thing = LRUCacheThing(items=1000)
        columns = self.data_columns()
        
        row_count = 1
        for row in self.data_rows(columns=columns, limit_count=limit_count):

            # skip the row and store it in an ImportSchemeRejectedRow if it's rejected
            if deep_exists(dictionary=row, keys=["***row***setting***", "reject_row"]):
                ImportSchemeRowRejected(import_scheme=self, errors=row["***row***setting***"]["reject_row"], row=row).save()

            # Use a transaction so each source row gets saved or not
            try:
                with transaction.atomic():
                    # Commit cache_thing changes if the transaction commits
                    transaction.on_commit(cache_thing.commit)

                    for app in importers[self.importer].apps:
                        working_objects: dict[str: dict[str: any]] = {}

                        for model in app.models_by_import_order:
                            working_attributes = {}
                            
                            superbreak: bool = False # Needed to break out of both for loops

                            # Step through fields and fill working_attributes
                            for field in model.fields:
                                if field.is_foreign_key():
                                    if field.field.related_model.__name__ in working_objects:
                                        working_attributes[field.name] = working_objects[field.field.related_model.__name__]
                                    else:
                                        working_attributes[field.name] = None
                                else:
                                    working_attributes[field.name] = row.get(field.name)

                            # Load instances per their unique fields until we run out of unique fields or an object is returned.
                            unique_sets: list[tuple] = list(model.model._meta.__dict__.get("unique_together"))
                            unique_sets = unique_sets + [(field.name,) for field in model.fields if field.field.unique and not field.is_foreign_key()]

                            for unique_set in unique_sets:
                                test_attributes: dict[str, any] = {}
                                test_attributes_string: str = ""

                                for unique_field in unique_set:
                                    test_attributes[getattr(unique_field, "name", unique_field)] = working_attributes[unique_field]
                                    test_attributes_string += f"|{unique_field}:{working_attributes[unique_field]}|"

                                working_objects[model.name] = cache_thing.find(key=(model.name, test_attributes_string), report=False)

                                if model.name not in working_objects or not working_objects[model.name]:
                                    working_objects[model.name] = model.model.objects.filter(**test_attributes).first()

                                    if working_objects[model.name]:
                                        cache_thing.store(key=(model.name, test_attributes_string), value=working_objects[model.name], transaction=True)

                                if working_objects[model.name]:
                                    continue
                        
                            # Ensure that if the data for a field is None that the field is nullable
                            if model.name not in working_objects:
                                for field in model.fields:
                                    if working_attributes[field.name] is None and field.not_nullable():

                                        working_objects[model.name] = None

                                        if model.settings.get("critical"):
                                            raise IntegrityError(f"Critical model is invalid: Model: {model.name}, Field: {field.name} is null")
                                        
                                        superbreak = True
                                        break
                            
                            if superbreak: 
                                continue

                            if not working_objects.get(model.name):
                                working_objects[model.name] = model.model(**working_attributes)
                                working_objects[model.name].save()

                                # If this is a deferred model save an ImportSchemeDeferredRows
                                if "restriction" in model.settings and model.settings["restriction"] == "deferred":

                                    if type(working_objects[model.name].pk) is int:
                                        ImportSchemeRowDeferred(import_scheme = self,
                                                                model = model.name,
                                                                pkey_name = working_objects[model.name]._meta.pk.name,
                                                                pkey_int = working_objects[model.name].pk,
                                        ).save()

                                    elif type(working_objects[model.name].pk) is str:
                                        ImportSchemeRowDeferred(import_scheme = self,
                                                                model = model.name,
                                                                pkey_name = working_objects[model.name].pk.name,
                                                                pkey_str = working_objects[model.name].pk,
                                        ).save()

            except IntegrityError as err:
                # Roll back cache_thing changes if the transaction is rolled back
                log.debug(err)
                cache_thing.rollback()
                #ImportSchemeRowRejected(import_scheme=self, errors="Row rejected due to query error or invalid null in critical model.", row=row).save()
                ImportSchemeRowRejected(import_scheme=self, errors=str(err), row=row).save()
        
            print(f"{row_count:,}")
            row_count += 1


class ImportSchemeFileStatus(ImportBaseModel):
    """ Holds statuses for ImportSchemeFiles """

    name = models.CharField(max_length=255)
    uploaded = models.BooleanField(default=False)
    preinspected = models.BooleanField(default=False)
    inspecting = models.BooleanField(default=False)
    inspected = models.BooleanField(default=False)
    importing = models.BooleanField(default=False)
    imported = models.BooleanField(default=False)


class ImportSchemeFile(ImportBaseModel):
    ''' Holds a file to import for an ImportScheme. '''

    name = models.CharField(max_length=255, null=False, blank=False)
    import_scheme = models.ForeignKey(ImportScheme, on_delete=models.CASCADE, related_name='files', editable=False)
    type = models.CharField(max_length=255)
    status = models.ForeignKey(ImportSchemeFileStatus, on_delete=models.DO_NOTHING, default=1, related_name="files")
    settings = models.JSONField(default=dict)

    @property
    def file_name(self) -> str:
        ''' Return a file name based on the ID of the ImportFile '''

        return str(self.id).rjust(8, '0')
    
    @property
    def row_count(self) -> int:
        """ Count the lines of the file """

        if self.base_type == "text":
            if self.settings.get("has_db", False):
                return sqlite3.connect(f"{settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name}.db").execute("SELECT COUNT(*) FROM data").fetchone()[0]
            else:
                return int(subprocess.check_output(['wc', '-l', settings.ML_IMPORT_WIZARD['Working_Files_Dir'] + self.file_name]).split()[0])
    
    @property
    def base_type(self) -> str:
        """ Returns the base type of the file: text or gff """

        if self.type.lower() in  ("gff", "gff3"):
            return "gff"
        elif self.type.lower() in ("tsv", "csv"):
            return "text"
    
    @property
    def ready_to_inspect(self) -> bool:
        """ Returns true if the file is ready to preinspect """

        if self.base_type == "gff":
            return False
            
        if self.base_type == "text":
            try:
                self._confirm_file_is_ready(preinspected=False, inspected=False)
            except:
                return False
            
            if self.settings.get("first_row_header", None) is None:
                return False

        return True

    def save(self, *args, **kwargs) -> None:
        ''' Override Save to get at the file type  '''

        self.type = Path(self.name).suffix[1:]
        
        if self.status == None:
            self.status = {}

        super().save(*args, **kwargs)

    def set_status_by_name(self, status):
        """ Looks up the status name and """

        try:
            status_object = ImportSchemeFileStatus.objects.get(name=status)
        except ImportSchemeFileStatus.DoesNotExist:
            raise StatusNotFound(f"ImportSchemeFileStatus {status} is not valid")
        
        self.status = status_object

    def import_fields(self, *, fields: dict=None) -> None:
        ''' Import the fields contained in the file, along with sample '''

        if fields is None: return
        
        for field, samples in fields.items():
            import_file_field = self.fields.create(name=field)
            import_file_field.import_sample(sample=samples)

    def inspect(self, *, use_db: bool = False, ignore_status: bool = False) -> None:
        """ Inspect the file to figure out what fields it has """
        
        if self.base_type == "gff":
            self._inspect_gff(use_db=use_db, ignore_status=ignore_status)

        elif self.base_type == "text":
            self._inspect_text(ignore_status=ignore_status)

    def rows(self, *, limit_count: int = 0, specific_rows: list[int] = None, header_row: bool = False, connection = None) -> dict[str: any]:
        """ Iterates through the rows of the file, returning a dict for each row """

        if self.base_type == "gff":
            for row in self._rows_gff(limit_count=limit_count, specific_rows=specific_rows):
                yield row

        elif self.base_type == "text":
            if self.settings.get("has_db", False):
                for row in self._rows_db(limit_count=limit_count, connection=connection):
                    yield row
            else:
                columns: list[str] = []
                if self.settings.get("first_row_header", False):
                    columns = self.header_fields()

                for row in self._rows_text(limit_count=limit_count, specific_rows=specific_rows, header_row=header_row):
                    if not len(columns):
                        for index, field in enumerate(row):
                            columns.append(f"Field {index+1}")

                    row_dict = {}
                    
                    for index, field in enumerate(row):
                        row_dict[columns[index]] = field;
                    yield row_dict

    def header_fields(self, *, connection = None) -> list:
        """ Return the first row of the file as a list """
        
        if self.base_type == "text":
            if self.settings.get("has_db", False):
                fields: list = []
                if not connection: 
                    connection = self._get_db_connection()

                for field in connection.execute("SELECT name FROM columns"):
                    fields.append(field["name"])
                return fields
            else:
                for fields in self._rows_text(header_row=True):
                    return fields

    def find_row_by_key(self, *, field: str = None, key: str = None, cache: LRUCacheThing = None, connection = None) -> list|None:
        """ Find the first row that has a field that equals key.  Uses a cache object if it's given one """

        if not field or not key: 
            return None

        if self.settings.get("has_db", False) and not connection: connection = self._get_db_connection()

        # If the data is a list step through the list and check each value
        if type(key) is list:
            row = None

            for item in key:
                row = self.find_row_by_key(field=field, key=item, cache=cache, connection=connection)
                if row:
                    break

            return row

        if cache:
            row = cache.find(key=key, report=True, output="log")
            if row:
                return row
            
        if self.base_type == "text":
            if self.settings.get("has_db", False):
                row = connection.execute(f"SELECT * FROM data WHERE \"{field}\"='{key}'").fetchone()
                return row
            else:
                for row in self.rows():
                    if cache: cache.store(key=key, value=row)
                    if row[field] == key:
                        return row
        
        # If it's not found after going through the file store that it's not in the file
        if cache:
            cache.store(key=key, value=None)

        return None

    def _rows_db(self, *, limit_count: int = 0, specific_rows: list[int] = None, header_row: bool = False, connection = None) -> list:
        """ Iterates through the rows of select from an SQLite3 db, returning a list for each row """

        if not connection: connection = self._get_db_connection()

        where_bit: str = ""
        limit_bit: str = ""

        if limit_count: limit_bit = f" LIMIT {limit_count} "
        if specific_rows: where_bit = f" WHERE rowid in ({','.join([str(row) for row in specific_rows])}) "

        sql = f"SELECT * FROM data{where_bit}{limit_bit}"

        for row in connection.execute(sql):
            yield row

    def _rows_text(self, *, limit_count: int = 0, specific_rows: list[int] = None, header_row: bool = False) -> list:
        """ Iterates through the rows of a text (csv or tsv) file, returning a list for each row """
    
        delimiter: str = "\t" if self.type.lower()=="tsv" else ","
        read_count: int = 0
        returned_count: int = 0
        skipped_header_row: bool = False
        has_header_row: bool = self.settings.get("first_row_header", False)

        if specific_rows is not None:
            max_specific_rows: int = max(specific_rows)
            specific_rows.sort()
        else:
            max_specific_rows = 0

        with open(f"{settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name}", "r") as file:
            reader = csv.reader(file, delimiter=delimiter)
            for row in reader:
                if not header_row and not skipped_header_row and has_header_row:
                    skipped_header_row = True
                    continue

                read_count += 1
                if not header_row and specific_rows is not None and read_count not in specific_rows:
                    continue
                
                yield row
                returned_count += 1

                if specific_rows is not None and returned_count > max_specific_rows:
                    break

                if limit_count and returned_count >= limit_count or header_row:
                    break

    def _rows_gff(self, *, limit_count: int = 0, specific_rows: list[int] = None) -> dict[str: any]:
        """ Iterates through the rows of the GFF file, returning a dict for each row """

        self._confirm_file_is_ready(inspected=True)

        db = gffutils.FeatureDB(f'{settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name}.db')

        base_fields = ('seqid', 'source', 'featuretype', 'start', 'end', 'score', 'strand', 'frame')
        counter: int = 1

        for feature in db.all_features():
            row: dict[str, any] = {}

            for field in base_fields:
                row[field] = getattr(feature, field)

            for key, value in feature.attributes.items():
                row[key] = value
                if len(row[key]) == 1: row[key] = row[key][0]

            yield row

            if limit_count:
                counter += 1
                if counter > limit_count:
                    break

    def _inspect_text(self, *, ignore_status: bool = False) -> None:
        """ Inspect a text file (tsv, csv) by importing to the db """
        
        self._confirm_file_is_ready(ignore_status=ignore_status, preinspected=True)

        self.set_status_by_name('Inspecting')
        self.save(update_fields=["status"])

        connection = self._create_text_db(replace_file=True)

        row_count = self.row_count
        
        # Look at 25 rows spread out in the file.
        attributes: dict = {}

        if self.settings["first_row_header"]:
            for attribute in self.header_fields(connection=connection):
                attributes[attribute] = set()

        specific_rows: list = None

        if self.settings["first_row_header"]:
            if row_count > 26:
                specific_rows = [int(row*(row_count-1)/25) for row in range(1, 26)]        
        else:
            if row_count > 25:
                specific_rows = [int(row*(row_count)/25) for row in range(1, 26)]
        
        for row in self.rows(specific_rows=specific_rows, connection=connection):
            for field, attribute in attributes.items():
                attribute.add(row[field])

        # Remove any existing fields
        self.fields.all().delete()
        
        self.import_fields(fields=attributes)

        self.set_status_by_name('Inspected')
        self.save(update_fields=["status"])

    def _inspect_gff(self, *, use_db: bool = False, ignore_status: bool = False) -> None:
        ''' Inspect a GFF file by importing to the db '''

        self._confirm_file_is_ready(ignore_status=ignore_status)

        self.set_status_by_name('Inspecting')
        self.save(update_fields=["status"])
        
        if (use_db):
            db = gffutils.FeatureDB(f'{settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name}.db')
        else:
            db = gffutils.create_db(
                f'{settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name}', 
                f'{settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name}.db', 
                merge_strategy="create_unique", 
                force=True
            )

        # Look at five of each featuretype to make a master list of attributes
        attributes: dict = {}

        fixed_attributes=('seqid', 'source', 'featuretype', 'start', 'end', 'score', 'strand', 'frame', 'bin')

        for feature_type in db.featuretypes():
            for feature in islice(db.features_of_type(featuretype=feature_type), 5):

                # Get the arbitrary attributes
                for attribute in feature.attributes:
                    if attribute in attributes:
                        attributes[attribute] = attributes[attribute] | set(feature.attributes[attribute])
                    else:
                        attributes[attribute] = set(feature.attributes[attribute])

                # Get the fixed attributes
                for attribute in fixed_attributes:
                    if attribute in attributes:
                        attributes[attribute].add(getattr(feature, attribute))
                    elif getattr(feature, attribute) is not None:
                        attributes[attribute] = set([getattr(feature, attribute)])

        # Remove any existing fields
        self.fields.all().delete()
        
        self.import_fields(fields=attributes)

        self.set_status_by_name('Inspected')
        self.save(update_fields=["status"])

    def _confirm_file_is_ready(self, *, ignore_status: bool = False, preinspected: bool = False, inspected: bool = False) -> None:
        """ Make sure that the file is ready to operate on """

        if self.type.lower() in  ("gff", "gff3"):
            # Gffutils is not installed
            if (NO_GFFUTILS):
                raise GFFUtilsNotInstalledError("gfutils is not installed: The file can't be inspected because GFFUtils is not installed. (pip install gffutils)")

        # File hasn't been marked as uploaded
        if not ignore_status and self.status.uploaded == False:
            raise FileNotReadyError(f'File not marked as saved: {self} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name})')

        # File is missing from disk
        if not os.path.exists(f"{settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name}"):
            raise FileNotReadyError(f"File is missing from disk: {self} ({settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name})")

        # File should be preinspected but isn't
        if not ignore_status and preinspected and self.status.preinspected == False:
            raise FileNotReadyError(f'File has not been preinspected: {self} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name})')
        
        # File shouldn't be inspected and is
        if not ignore_status and not inspected and self.status.inspected == True:
            raise FileNotReadyError(f'File already inspected: {self} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name})')
        
        # File should be inspected and isn't
        if not ignore_status and inspected and self.status.inspected == False:
            raise FileNotReadyError(f'File has not been inspected: {self} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name})')

        if self.type.lower() in  ("gff", "gff3"):
            # File is inspected, but DB is missing from disk
            if not ignore_status and inspected and not os.path.exists(f"{settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name}.db"):
                raise FileNotReadyError(f"DB file is missing from disk: {self} ({settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name}.db)")
    
    def _create_text_db(self, *, replace_file: bool = False) -> None:
        """ Build a SQLite3 DB for inspecting and importing the file """

        if os.path.isfile(f"{settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name}.db") and os.stat(f"{settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name}.db").st_size:
            if replace_file:
                os.remove(f"{settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name}.db")
            else:
                raise FileExistsError(f"SQLite3 DB already exists: {settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name}.db")

        self.settings["has_db"] = False

        connection = self._get_db_connection()
        #cursor = connection.cursor()

        columns: list = self.header_fields()
        sql: str = ""

        # Set up columns table to hold info on the columns.  Convert columns to a list of tuples
        connection.execute("CREATE TABLE columns(name)")
        connection.executemany("INSERT INTO columns VALUES(?)", [(column,) for column in columns])

        # Create a data table to hold the actual data
        column_list: str = ", ".join([f'\"{column}\"' for column in columns])
        connection.execute(f"CREATE TABLE data({column_list})")

        sql = f"INSERT INTO data VALUES({', '.join(['?' for column in columns])})"
        for row in self._rows_text():
            connection.execute(sql, row)

        connection.commit()

        self.settings["has_db"] = True
        self.save(update_fields=["settings"])

        return connection
    
    def _get_db_connection(self) -> None:
        """ Returns a SQLite3 connection for loading or reading data """

        connection = sqlite3.connect(f"{settings.ML_IMPORT_WIZARD['Working_Files_Dir']}{self.file_name}.db")
        connection.row_factory = sqlite3.Row

        return connection
    
    # Put on hold until I see what the performance is like
    # @timeit(output="log")
    # def _create_db_index(self, *, field: str) -> None:
    #     """ Creates an index on the data table """
        
    #     index_name = f"field"

class ImportSchemeFileField(ImportBaseModel):
    ''' Describes a field for an ImportFile '''

    import_scheme_file = models.ForeignKey(ImportSchemeFile, related_name='fields', on_delete=models.CASCADE, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    sample = models.TextField(null=True, blank=True)

    # class Meta:
    #     ordering = [Lower('name')]

    @property
    def fancy_name(self) -> str:
        """ Returns the 'fancy name' of the item.  Words separated by spaces, and initial caps """

        return fancy_name(self.name)
    
    @property
    def short_sample(self) -> str:
        """ Returns only 80 characters of the sample, with elipses if it's cut off """

        if len(self.sample) <= 80: return self.sample
        return f"{self.sample[:77]}..."
        

    def import_sample(self, *, sample: any=None) -> None:
        ''' Import the Sample data and massage it by type '''

        self.sample = stringalize(sample)

        self.save(update_fields=["sample"])


class ImportSchemeItem(ImportBaseModel):
    """ Holds Import Items """

    import_scheme = models.ForeignKey(ImportScheme, on_delete=models.CASCADE, related_name='items', null=True, editable=False)
    app = models.CharField("App this import item is for", max_length=255)
    model = models.CharField("Model this import item is for", max_length=255)
    field = models.CharField("DB Field this import item is for", max_length=255)
    strategy = models.CharField("Strategy for doing this import", max_length=255, null=True)
    settings = models.JSONField("Settings specific to this import", default=dict)
    added = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    @property
    def name(self) -> str:
        """ Custom name for the ImportSchemeItem """
        return f"{self.app}{self.model}{self.field}"

    class Meta:
        unique_together = ["import_scheme", "app", "model", "field"]


class ImportSchemeRowRejected(ImportBaseModel):
    """ Holds all rejected rows for an import, and the reason they were rejected """

    import_scheme = models.ForeignKey(ImportScheme, on_delete=models.CASCADE, related_name='rejected_rows', null=True, editable=False)
    errors = models.JSONField("Why was this row rejected by the importer?")
    row = models.JSONField("Complete data for the row that was rejected")

    @property
    def name(self) -> str:
        """ Custom name for ImportSchemeRejectedRow"""
        return f"Rejected row for {self.model}"


class ImportSchemeRowDeferred(ImportBaseModel):
    """ Holds refrences to rows that have been deferred for approval """
    
    import_scheme = models.ForeignKey(ImportScheme, on_delete=models.CASCADE, related_name='deferred_rows', null=True, editable=False)
    model = models.TextField(max_length=255, null=False)
    pkey_name = models.CharField(max_length=255, default="pk", null=False)
    pkey_int = models.IntegerField(null=True)
    pkey_str = models.TextField(null=True)