from django.conf import settings
from django.db import models

from pathlib import Path

from .tools import dict_hash


class ImportBaseModel(models.Model):
    ''' A base class to hold comon methods and attributes.  It's Abstract so Django won't make a table for it
    The # pragma: no cover keeps the lines from being counted in coverage percentages '''

    id = models.BigAutoField(primary_key=True)

    class Meta:
        abstract = True
    
    def __str__(self) ->str:
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
    importer = models.CharField(max_length=255, null=False, blank=False)
    importer_hash = models.CharField(max_length=32)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.IntegerField(choices=STATUSES, default=0)
    public = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
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
        (2, 'Inspeting'),
        (3, 'Inspected'),
        (4, 'Importing'),
        (5, 'Imported'),
    ]

    @classmethod
    def status_from_label(cls, label) -> str:
        ''' Returns the status value by lable '''

        return next(key for key, value in dict(cls.STATUSES).items() if value.lower() == label.lower())

    name = models.CharField(max_length=255, null=False, blank=False)
    import_scheme = models.ForeignKey(ImportScheme, on_delete=models.CASCADE, related_name='files')
    type = models.CharField(max_length=255)
    status = models.IntegerField(choices=STATUSES, default=0)

    @property
    def file_name(self) -> str:
        ''' Return a file name based on the ID of the ImportFile '''

        return str(self.id).rjust(8, '0')
    
    def save(self, *args, **kwargs):
        ''' Override Save to get at the file type  '''

        self.type = Path(self.name).suffix[1:]

        super().save(*args, **kwargs)


class ImportSchemeItem(ImportBaseModel):
    ''' Holds Import Items '''

    name = models.CharField(max_length=255, null=False, blank=False)
    import_scheme = models.ForeignKey(ImportScheme, on_delete=models.CASCADE, related_name='items', null=True)
    import_scheme_item = models.ForeignKey('self', on_delete=models.CASCADE, related_name='items', null=True)
    added_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True)