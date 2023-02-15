from django.db import models

class ImportBaseModel(models.Model):
    ''' A base class to hold comon methods and attributes.  It's Abstract so Django won't make a table for it
    The # pragma: no cover keeps the lines from being counted in coverage percentages '''
    class Meta:
        abstract = True
    
    def __str__(self) ->str:
        ''' Generic stringify function.  Most objects will have a name so it's the default. '''
        return self.name                    # type: ignore   # pragma: no cover


class ImportScheme(ImportBaseModel):
    '''  Import scheme holds all required information to import a file '''
    name = models.CharField(max_length=255, null=False, blank=False)
    hash = models.CharField(max_length=32, null=False, blank=False)
    
