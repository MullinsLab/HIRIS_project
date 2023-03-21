from django.conf import settings
from django.db import models
from django.db.models.functions import Lower

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from pathlib import Path
from itertools import islice
import json

# Check to see if gffutils is installed
NO_GFFUTILS: bool = False
from importlib.util import find_spec
if (find_spec("gffutils")): import gffutils 
else: NO_GFFUTILS=True

from ml_import_wizard.utils.simple import dict_hash, stringalize, fancy_name
from ml_import_wizard.exceptions import GFFUtilsNotInstalledError, FileNotSavedError, FileHasBeenInspectedError, FileNotInspectedError
from ml_import_wizard.utils.importer import importers


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


class ImportScheme(ImportBaseModel):
    '''  Import scheme holds all required information to import a specific file format. FIELDS:(name, importer, user) '''

    STATUSES: list[tuple] = [
        (0, 'New'),
        (1, 'File Received'),
    ]

    @classmethod
    def status_from_label(cls, label) -> str:
        ''' Returns the status value by lable '''

        return next(key for key, value in dict(cls.STATUSES).items() if value.lower() == label.lower())
    
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    importer = models.CharField(max_length=255, null=False, blank=False, editable=False)
    importer_hash = models.CharField(max_length=32, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.IntegerField(choices=STATUSES, default=0)
    public = models.BooleanField(default=True)

    def save(self, *args, **kwargs) -> None:
        ''' Override Save to store the importer_hash.  This is used to know if the Importer definition has changed, invalidating this importer  '''

        if not self.importer_hash:
            self.importer_hash = dict_hash(settings.ML_IMPORT_WIZARD['Importers'][self.importer])
        super().save(*args, **kwargs)

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

        dirty = item.set_with_dirty("strategy", strategy)
        dirty = item.set_with_dirty("settings", settings)

        if dirty: item.save()

        return item
    
    def preview_data_table(self, limit_count: int=100) -> dict:
        """ Get preview data for showing to the user """
        
        log.debug("getting preview data table.")

        table: dict = {"columns": self.data_columns(),
                       "rows": []            
        }

        for row in self.data_rows(columns = table["columns"], limit_count=limit_count):
            table["rows"].append(row)

        # log.debug(f"data length: {len(table['data'])}")
        # log.debug(json.dumps(table["data"]))
        # log.debug(json.dumps(table["columns"]))

        return table

    def data_columns(self) -> list[dict[str: any]]:
        """ Returns a list of columns each set of models in the target importer """
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

                    column_id += 1
        return columns
    
    def data_rows(self, *, columns: list = [], limit_count: int = None) -> dict[str: any]:
        """ Yields a row for each set of models in the target importer """
        fields: dict[int: any] = {}
        if not columns:
            columns = self.data_columns
        
        for import_scheme_file in self.files.all():
            for row in import_scheme_file.rows(limit_count=limit_count):
                row_dict: dict = {}

                for column in columns:    
                    strategy = column["import_scheme_item"].strategy
                    settings = column["import_scheme_item"].settings

                    if strategy == "Raw Text":
                        row_dict[column["name"]] = settings["raw_text"]

                    elif strategy == "Table Row":
                        row_dict[column["name"]] = settings["row"]

                    elif strategy == "File Field":
                        if settings["key"] not in fields:
                            import_scheme_file_field = ImportSchemeFileField.objects.get(pk=settings["key"])
                            fields[import_scheme_file_field.id] = import_scheme_file_field.name
                            
                        row_dict[column["name"]] = row[fields[settings["key"]]]
                    
                    elif strategy == "Split Field":
                        if settings["split_key"] not in fields:
                            import_scheme_file_field = ImportSchemeFileField.objects.get(pk=settings["split_key"])
                            fields[import_scheme_file_field.id] = import_scheme_file_field.name
                        
                        value = row[fields[settings["split_key"]]]

                        if settings["splitter"] in value:
                            row_dict[column["name"]] = value.split(settings["splitter"])[settings["splitter_position"]-1]
                        else:
                            row_dict[column["name"]] = value

                yield row_dict

class ImportSchemeFile(ImportBaseModel):
    ''' Holds a file to import for an ImportScheme. '''

    STATUSES: list[tuple] = [
        (0, 'New'),
        (1, 'Uploaded'),
        (2, 'Inspecting'),
        (3, 'Inspected'),
        (4, 'Importing'),
        (5, 'Imported'),
    ]

    @classmethod
    def status_from_label(cls, label) -> str:
        ''' Returns the status value by lable '''

        return next(key for key, value in dict(cls.STATUSES).items() if value.lower() == label.lower())

    name = models.CharField(max_length=255, null=False, blank=False)
    import_scheme = models.ForeignKey(ImportScheme, on_delete=models.CASCADE, related_name='files', editable=False)
    type = models.CharField(max_length=255)
    status = models.IntegerField(choices=STATUSES, default=0)

    @property
    def file_name(self) -> str:
        ''' Return a file name based on the ID of the ImportFile '''

        return str(self.id).rjust(8, '0')
    
    def save(self, *args, **kwargs) -> None:
        ''' Override Save to get at the file type  '''

        self.type = Path(self.name).suffix[1:]

        super().save(*args, **kwargs)

    def import_fields(self, *, fields: dict=None) -> None:
        ''' Import the fields contained in the file, along with sample '''

        if fields is None: return
        
        for field, samples in fields.items():
            import_file_field = self.fields.create(name=field)
            import_file_field.import_sample(sample=samples)

    def _confirm_file_is_ready(self, *, ignore_status: bool = False, inspected: bool = False) -> None:
        """ Make sure that the file is ready to operate on """

        # Error out if gffutils is not installed
        if (NO_GFFUTILS):
            raise GFFUtilsNotInstalledError("gfutils is not installed: The file can't be inspected because GFFUtils is not installed. (pip install gffutils)")

        # Error out if the file hasn't been uploaded
        if not ignore_status and self.status == 0:
            raise FileNotSavedError(f'File not marked as saved: {self} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name})')
        
        # Error out if the file shouldn't be inspected and is
        if not ignore_status and not inspected and self.status >= 3:
            raise FileHasBeenInspectedError(f'File already inspected: {self} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name})')
        
        # Error out if the file should be inspected and isn't
        if not ignore_status and inspected and self.status < 3:
            raise FileNotInspectedError(f'File has not been inspected: {self} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.file_name})')
        

    def rows(self, *, limit_count: int = 0) -> dict[str: any]:
        """ Iterates through the rows of the file, returning a dict for each row """

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

    def inspect(self, *, use_db: bool = False, ignore_status: bool = False) -> None:
        ''' Inspect the file by importing to the db '''

        self._confirm_file_is_ready(ignore_status=ignore_status)

        self.status = self.status_from_label('Inspecting')
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

        self.status = self.status_from_label('Inspected')
        self.save(update_fields=["status"])


class ImportSchemeFileField(ImportBaseModel):
    ''' Describes a field for an ImportFile '''

    import_scheme_file = models.ForeignKey(ImportSchemeFile, related_name='fields', on_delete=models.CASCADE, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    sample = models.TextField(null=True, blank=True)

    class Meta:
        ordering = [Lower('name')]

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
    ''' Holds Import Items '''

    import_scheme = models.ForeignKey(ImportScheme, on_delete=models.CASCADE, related_name='items', null=True, editable=False)
    app = models.CharField("App this import item is for", max_length=255)
    model = models.CharField("Model this import item is for", max_length=255)
    field = models.CharField("DB Field this import item is for", max_length=255)
    strategy = models.CharField("Strategy for doing this import", max_length=255, null=True)
    # import_scheme_file = models.ForeignKey(ImportSchemeFile, on_delete=models.CASCADE, null=True, blank=True)
    settings = models.JSONField("Settings specific to this import", null=True)
    added = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = ["app", "model", "field"]
        