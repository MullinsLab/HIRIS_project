from django.conf import settings

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])


class LoggingException(Exception):
    """ Class to inherit if we want exceptions logged """
    def __init__(self, message: str=''):
        log.warn(message)
        self.message = message

    def __str__(self) -> str:
        return self.message
    

class GFFUtilsNotInstalledError(LoggingException):
    """ GFF & GFF3 Files can't be inspected because gffutils is not installed """


class FileNotSavedError(LoggingException):
    """ File can't be operated on because it hasn't been saved. """


class FileHasBeenInspectedError(LoggingException):
    """ File can't be operated on because it has already been inspected. """


class FileNotInspectedError(LoggingException):
    """ File can't be operated on because it has not been inspected """