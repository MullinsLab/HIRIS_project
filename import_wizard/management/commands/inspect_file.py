from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import logging
log = logging.getLogger(settings.IMPORT_WIZARD['Logger'])

from import_wizard.models import ImportFile
from import_wizard.utils.gff import FileNotSavedError, FileHasBeenInspectedError, GFFImporter

class Command(BaseCommand):
    help = "Inspects a file in preperation for importing. This is not intended to be run by humans, it's there for the system to run outside of page views. "
    suppressed_base_arguments = ['--traceback', '--settings', '--pythonpath', '--skip-checks', '--no-color', '--version', '--force-color']

    def add_arguments(self, parser):
        ''' Set the arguments for InspectFile '''
        parser.add_argument('import_file_id', nargs='+', type=int, help='The ID(s) of the ImportFile(s) to inspect')

        parser.add_argument(
            '--use_db',
            action='store_true',
            help="Use the existing DB instead of building a new one (only for GFF and GFF3 files).",
        )

        parser.add_argument(
            '--ignore_status',
            action='store_true',
            help="Inspect the file even if it has already been inspected.",
        )

    def handle(self, *args, **options):
        ''' Do the work of inspecting a file '''
        
        files_count: int = 0
        verbosity: int = int(options['verbosity'])

        for import_file_id in options['import_file_id']:
            try:
                import_file = ImportFile.objects.get(pk=import_file_id)
            except ImportFile.DoesNotExist:
                raise CommandError(f'ImportFile {import_file_id} does not exist')

            # Create the importer based on the type of the file
            if import_file.type in ['gff', 'gff3']:
                log.debug('Got gff file type for inspection')
                file_importer = GFFImporter(import_file=import_file, use_db=options['use_db'], ignore_status=options['ignore_status'])
            
            if verbosity > 1:
                self.stdout.write(f'Starting to inspect {import_file} ({settings.IMPORT_WIZARD["Working_Files_Dir"]}{import_file.file_name}) file.')

            try:
                file_importer.inspect()
            except FileNotSavedError as err:
                raise CommandError(err)
            except FileHasBeenInspectedError as err:
                raise CommandError(err)
            
            if verbosity > 1:
                self.stdout.write(f'You done inspected that {import_file} ({settings.IMPORT_WIZARD["Working_Files_Dir"]}{import_file.file_name}) file!')

            files_count += 1

        if not files_count: self.stdout.write(self.style.FAILURE(f'No files inspected.'))
        elif files_count == 1: self.stdout.write(self.style.SUCCESS(f'1 file inspected.'))
        else: self.stdout.write(self.style.SUCCESS(f'{files_count} files inspected.'))
