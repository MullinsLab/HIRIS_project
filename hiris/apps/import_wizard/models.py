from django.conf import settings
from django.db import models
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

    name = models.CharField(max_length=255, null=False, blank=False)
    importer = models.CharField(max_length=255, null=False, blank=False)
    importer_hash = models.CharField(max_length=32)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        ''' Override Save to store the importer_hash.  This is used to know if the Importer definition has changed, invalidating this importer  '''

        if not self.importer_hash:
            self.importer_hash = dict_hash(settings.IMPORT_WIZARD['Importers'][self.importer])
        super().save(*args, **kwargs)


class ImportFile(ImportBaseModel):
    ''' Holds a file to import for an ImportScheme. FIELDS: (name, import_scheme, location) '''

    name = models.CharField(max_length=255, null=False, blank=False)
    import_scheme = models.ForeignKey(ImportScheme, on_delete=models.CASCADE, related_name='files')
    file_type = models.CharField(max_length=255)

    @property
    def file_name(self) -> str:
        ''' Return a file name based on the ID of the ImportFile '''

        return str(self.id).rjust(8, '0')