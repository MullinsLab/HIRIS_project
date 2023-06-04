from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from hiris.apps.core.utils.db import process_integration_feature_links
from hiris.apps.core.utils.backend import fill_publication_data


class Command(BaseCommand):
    help = " Link the integrations to features and get publication data from Pubmed.  Needs to run after each import "
    suppressed_base_arguments = ['--traceback', '--settings', '--pythonpath', '--skip-checks', '--no-color', '--version', '--force-color']

    def handle(self, *args, **options):
        """ Link the integrations to features and get publication data from Pubmed """

        fill_publication_data()
        print("Completed filling publication data.")

        process_integration_feature_links()
        print("Completed processing integration feature links.")

        self.stdout.write(self.style.SUCCESS(f'After import processes complete.'))