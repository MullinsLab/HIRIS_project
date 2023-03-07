from django.conf import settings
from django.views.generic.base import View
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string

import os
import json
import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard.forms import UploadFileForImportForm, NewImportSchemeForm
from ml_import_wizard.models import ImportScheme, ImportSchemeFile, ImportSchemeItem
from ml_import_wizard.utils.simple import sound_user_name
from ml_import_wizard.utils.inspect import inspect_models

class ManageImports(LoginRequiredMixin, View):
    ''' The starting place for importing.  Show information on imports, started imports, new import, etc. '''

    def get(self, request, *args, **kwargs):
        ''' Handle a get request.  Returns a starting import page. '''
        importers: list[dict] = []
        user_import_schemes: list[dict] = []

        # Bring in the importers from settings
        for importer, importer_dict in settings.ML_IMPORT_WIZARD['Importers'].items():
            importer_item: dict[str] = {
                'name': importer_dict.get('long_name', importer_dict['name']),
                'importer': importer, # Used for URLs
            }

            if description := importer_dict.get('description'): importer_item['description'] = description

            importers.append(importer_item)

        # Show Import Schemes that this user owns
        for import_scheme in ImportScheme.objects.filter(user_id=request.user.id):
            user_import_scheme_item: dict = {
                'name': import_scheme.name,
                'id': import_scheme.id,
                'importer': import_scheme.importer,
                'description': import_scheme.description,
            }

            user_import_schemes.append(user_import_scheme_item)
 
        return render(request, "ml_import_wizard/manager.django-html", context={'importers': importers, 'user_import_schemes': user_import_schemes})


class NewImportScheme(LoginRequiredMixin, View):
    ''' View for creating a new import '''

    def get(self, request, *args, **kwargs):
        ''' Build a new Import '''
    
        importer: str = kwargs['importer_slug']
        importer_name: str = settings.ML_IMPORT_WIZARD['Importers'][importer]['name']

        return render(request, "ml_import_wizard/new_scheme.django-html", context={
            'form': NewImportSchemeForm(importer_slug=importer, initial={'name': f"{sound_user_name(request.user)}'s {importer_name} import"}), 
            'importer': importer_name
        })
    
    
    def post(self, request, *args, **kwargs):
        ''' Save the new import '''

        importer: str = kwargs["importer_slug"]
        form: form = NewImportSchemeForm(request.POST)

        if form.is_valid():
            import_scheme = ImportScheme(name=form.cleaned_data['name'], description=form.cleaned_data['description'], importer=importer, user=request.user)
            import_scheme.save()
            log.debug(f'Stored ImportScheme with PKey of {import_scheme.id}')

            request.session['current_import_scheme_id'] = import_scheme.id
            
            inspect_models(import_scheme_id=import_scheme.id)

            return HttpResponseRedirect(reverse('ml_import_wizard:scheme', kwargs={'import_scheme_id': import_scheme.id}))
        
        else:
            # Needs to have a better error
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))


class DoImportScheme(View):
    ''' Do the actual import stuff '''

    def get(self, request, *args, **kwargs):
        ''' Do the actual import stuff '''
        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))

        # Return the user to the /import page if they don't have a valid import_scheme_id to work on
        if import_scheme_id is None:
            log.debug('Got bad import_scheme_id')
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))

        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))
        
        request.session['current_import_scheme_id'] = import_scheme_id

        actions: list = []
        # First make sure that there is one or more file to work from
        if import_scheme.files.count() == 0:
            action: dict = {
                'name': 'No data file',
                'description': "You'll need one or more files to import data from.",
                'urgent': True,
                'start_expanded': True,
            }
            actions.append(action)

        return render(request, 'ml_import_wizard/scheme.django-html', context={
            'importer': settings.ML_IMPORT_WIZARD['Importers'][import_scheme.importer]['name'], 
            'import_scheme': import_scheme, 
            'actions': actions}
        )
    
    
class ListImportSchemeItems(LoginRequiredMixin, View):
    '''' List the ImportSchemeItems for a particular ImportScheme '''

    def get(self, request, *args, **kwargs):
        ''' Produce the list of ImportSchemeItems  '''

        import_scheme = ImportScheme.objects.get(pk=kwargs['import_scheme_id'])
        # Initialize with a 0 for 
        import_scheme_items: list[int] = [0]

        if import_scheme.files.count():
            for item in import_scheme.items.all():

                # Refactor me when you have a better idea of where we're going
                if item.name == "app":
                    for model in item.items.filter(name="model"):
                        import_scheme_items.append(model.id)

        return JsonResponse({
            'import_scheme_items': import_scheme_items
        })

    
class DoImportSchemeItem(LoginRequiredMixin, View):
    ''' Show and store ImportItems '''

    def get(self, request, *args, **kwargs):
        ''' Get information about an Import Item '''

        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))
        import_item_id: int = kwargs['import_item_id']

        return_data: dict = {}

        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))
        
        if (import_item_id == 0):
            # import_item_id 0 always refers to associated files
            if import_scheme.files.count() == 0:
                return_data = {
                    'name': 'No data file',
                    'description': "You'll need one or more files to import data from.",
                    'form': render_to_string('ml_import_wizard/fragments/scheme_file.django-html', request=request, context={
                        'form': UploadFileForImportForm(), 
                        'path': reverse('ml_import_wizard:scheme_item', kwargs={'import_scheme_id': import_scheme.id, 'import_item_id': 0})
                    }),
                    'urgent': True,
                    'start_expanded': True,
                }
            else:
                if import_scheme.files.count() == 1:
                    return_data = {
                        'name': '1 file uploaded',
                        'description': 'There is 1 file uploaded for this import:',
                    }
                else:
                    return_data = {
                        'name': f'{import_scheme.files.count()} files uploaded',
                        'description': f'There are {import_scheme.files.count()} files uploaded for this import:',
                    }
                    
                return_data['description'] += f'<ul><li>{import_scheme.list_files(separator="</li><li>")}</li></ul>'
        else:
            # Import items that aren't files
            item = ImportSchemeItem.objects.get(pk=import_item_id)
            return_data = {
                'name': item.fancy_value,
                'description': item.items_for_html(),
            }

        log.debug(f'Sending ImportSchemeItem via AJAX query: {return_data}')      
        return JsonResponse(return_data)   


    def post(self, request, *args, **kwargs):
        ''' Save or create an Import Item '''
        
        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))
        import_item_id: int = kwargs['import_item_id']

        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('ml_import_wizard:import'))

        if (import_item_id == 0):
            ''' import_item_id 0 always refers to associated files '''
            form: form = UploadFileForImportForm(request.POST, request.FILES)
            file: file = request.FILES['file']

            if form.is_valid():
                import_file = ImportSchemeFile(name=file.name, import_scheme=import_scheme)
                import_file.save()
                log.debug(f'Stored ImportFile with PKey of {import_file.id}')

                log.debug(f'Getting ready to store file at: {settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{import_file.file_name}')
                with open(settings.ML_IMPORT_WIZARD["Working_Files_Dir"] + import_file.file_name, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                log.debug(f'Stored file at: {settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{import_file.file_name}')

                import_file.status = ImportSchemeFile.status_from_label('Uploaded')
                import_file.save(update_fields=["status"])
                
                os.popen(os.path.join(settings.BASE_DIR, 'manage.py inspect_file ') + str(import_file.id))
                
                return JsonResponse({
                    'saved': True,
                })