from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard.utils.inspect import inspect_models


class Command(BaseCommand):
    def handle(self, *args, **options):
        inspect_models(import_scheme_id=1)