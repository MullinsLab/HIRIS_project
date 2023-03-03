import gffutils
from ..models import ImportFile

class GFFImporter():
    ''' Object to work with a GFF file. '''

    def __init__(self, *args, **kwargs):
        ''' Build the object '''