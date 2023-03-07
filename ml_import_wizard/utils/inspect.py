from django.conf import settings

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from itertools import islice

# Check to see if gffutils is installed
NO_GFFUTILS: bool = False
from importlib.util import find_spec
if (find_spec("gffutils")): import gffutils 
else: NO_GFFUTILS=True

from ml_import_wizard.models import ImportScheme, ImportSchemeFile, ImportSchemeItem
from ml_import_wizard.exceptions import GFFUtilsNotInstalledError, FileNotSavedError, FileHasBeenInspectedError
from ml_import_wizard.utils.simple import stringalize

# Should probably move to being a function since it is only interacted with once.
class GFFImporter():
    ''' Object to work with a GFF file. '''

    def __init__(self, import_file: ImportSchemeFile = None, use_db: bool = False, ignore_status: bool = False) -> None:
        ''' Build the object
        args: import_file = the ImportFile object to work with. '''

        # Error out if gffutils is not installed
        if (NO_GFFUTILS):
            raise GFFUtilsNotInstalledError("gfutils is not installed: The file can't be inspected because GFFUtils is not installed. (pip install gffutils)")

        #self.import_file = kwargs['import_file']
        self.import_file = import_file
        self.use_db = use_db
        self.ignore_status = ignore_status

    def inspect(self) -> None:
        ''' Inspect the file by importing to the db '''

        # Error out if the file hasn't been uploaded, or has already been inspected
        if not self.ignore_status and self.import_file.status == 0:
            raise FileNotSavedError(f'File not marked as saved: {self.import_file} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.import_file.file_name})')
        
        if not self.ignore_status and self.import_file.status >= 3:
            raise FileHasBeenInspectedError(f'File already inspected: {self.import_file} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.import_file.file_name})')
        
        self.import_file.status = ImportSchemeFile.status_from_label('Inspecting')
        self.import_file.save(update_fields=["status"])
        
        if (self.use_db):
            db = gffutils.FeatureDB(f'{settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.import_file.file_name}.db')
        else:
            db = gffutils.create_db(
                f'{settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.import_file.file_name}', 
                f'{settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{self.import_file.file_name}.db', 
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


        self.import_file.import_fields(fields=attributes)

        self.import_file.status = ImportSchemeFile.status_from_label('Inspected')
        self.import_file.save(update_fields=["status"])