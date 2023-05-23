from django.conf import settings

import logging
log = logging.getLogger(settings.ML_EXPORT_WIZARD['Logger'])

import inspect

class LoggingException(Exception):
    """ Class to inherit if we want exceptions logged """
    def __init__(self, message: str=''):
        message = f"{inspect.stack()[1].filename}:{inspect.stack()[1].lineno} ({inspect.stack()[1].function}) {message}"
        log.warn(message)
        self.message = message

    def __str__(self) -> str:
        return self.message
    

class MLExportWizardNoFieldFound(LoggingException):
    """ A field (or app or model) was requested that doesn't exist """