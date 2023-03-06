from django.conf import settings
from django.db import models

from pathlib import Path

from .utils.simple import dict_hash


class ImportBaseModel(models.Model):
    ''' A base class to hold comon methods and attributes.  It's Abstract so Django won't make a table for it
    The # pragma: no cover keeps the lines from being counted in coverage percentages '''

    id = models.BigAutoField(primary_key=True, editable=False)

    class Meta:
        abstract = True
    
    def __str__(self) -> str:
        ''' Generic stringify function.  Most objects will have a name so it's the default. '''
        return self.name                    # type: ignore   # pragma: no cover


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
            self.importer_hash = dict_hash(settings.IMPORT_WIZARD['Importers'][self.importer])
        super().save(*args, **kwargs)

    def list_files(self, *args, **kwargs) -> str:
        ''' Return a string that contains a list of file names for this ImportScheme 
        kwargs = separator '''

        separator: str = kwargs.get('separator', ', ')
        file_list: list[str] = []
        
        for file in self.files.all():
            file_list.append(file.name)

        return separator.join(file_list)


class ImportFile(ImportBaseModel):
    ''' Holds a file to import for an ImportScheme. FIELDS: (name, import_scheme, location) '''

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

    def import_fields(self, fields: dict=None) -> None:
        ''' Import the fields contained in the file, along with sample '''

        if fields is None: return
        
        for field, samples in fields.items():
            import_file_field = self.fields.create(name=field)
            import_file_field.import_sample(sample=samples)


class ImportFileField(ImportBaseModel):
    ''' Describes a field for an ImportFile '''

    import_file = models.ForeignKey(ImportFile, related_name='fields', on_delete=models.CASCADE, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    sample = models.TextField(null=True, blank=True)

    def import_sample(self, sample: any=None) -> None:
        ''' Import the Sample data and massage it by type '''

        print(f'Type of Sample:{type(sample)}')

        if type(sample) in [tuple, list, set]:
            #self.sample = ', '.join(f"'{item}'" for item in sample)
            self.sample = ', '.join(sample)
        elif type(sample) == str:
            self.sample = sample
        elif type(sample) == int:
            self.sample=str(sample)

        self.save(update_fields=["sample"])


class ImportSchemeItem(ImportBaseModel):
    ''' Holds Import Items '''

    name = models.CharField(max_length=255, null=False, blank=False)
    import_scheme = models.ForeignKey(ImportScheme, on_delete=models.CASCADE, related_name='items', null=True, editable=False)
    import_scheme_item = models.ForeignKey('self', on_delete=models.CASCADE, related_name='items', null=True, editable=False)
    added_date = models.DateField(auto_now_add=True, editable=False)
    updated_date = models.DateField(auto_now=True, editable=False)