from django.conf import settings
from django.views.generic.base import View
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

import logging
log = logging.getLogger(settings.IMPORT_WIZARD['Logger'])

from .forms import UploadFileForImportForm, NewImportSchemeForm
from .models import ImportScheme, ImportFile
from .tools import sound_user_name

class ManageImports(LoginRequiredMixin, View):
    ''' The starting place for importing.  Show information on imports, started imports, new import, etc. '''

    def get(self, request, *args, **kwargs):
        ''' Handle a get request.  Returns a starting import page. '''
        importers: list[dict] = []
        user_import_schemes: list[dict] = []

        # Bring in the importers from settings
        for importer, importer_dict in settings.IMPORT_WIZARD['Importers'].items():
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

        return render(request, "import_manager.django-html", {'importers': importers, 'user_import_schemes': user_import_schemes})


class NewImportScheme(LoginRequiredMixin, View):
    ''' View for creating a new import '''

    def get(self, request, *args, **kwargs):
        ''' Build a new Import '''
        
        importer: str = kwargs['importer_slug']
        importer_name: str = settings.IMPORT_WIZARD['Importers'][importer]['name']

        return render(request, "new_import.django-html", {
            'form': NewImportSchemeForm(importer_slug=importer, initial={'name': f"{sound_user_name(request.user)}'s {importer_name} import"}), 
            'importer': importer_name
        })
    
    def post(self, request, *args, **kwargs):
        ''' Save the new import '''

        form: form = NewImportSchemeForm(request.POST)
        importer: str = kwargs['importer_slug']

        if form.is_valid():
            import_scheme = ImportScheme(name=form.cleaned_data['name'], description=form.cleaned_data['description'], importer=importer, user=request.user)
            import_scheme.save()
            log.debug(f'Stored ImportScheme with PKey of {import_scheme.id}')

            request.session['current_import_scheme_id'] = import_scheme.id

            return HttpResponseRedirect(reverse('import_wizard:do_import', kwargs={'import_scheme_id': import_scheme.id}))
        
        else:
            # Needs to have a better error
            return HttpResponseRedirect(reverse('import_wizard:import'))
            
    
    
# class FileUpload(LoginRequiredMixin, View):
#     ''' Receive an uploaded file '''

#     def get(self, request, *args, **kwargs):
#         ''' Build a new Import '''
        
#         importer: str = kwargs['importer_slug']

#         return render(request, "new_import.django-html", {'form': UploadFileForImportForm(), 'importer': settings.IMPORT_WIZARD['Importers'][importer]['name']})

#     def post(self, request, *args, **kwargs):
#         ''' Get the file for a new import '''

#         form: form = UploadFileForImportForm(request.POST, request.FILES)
#         importer: str = kwargs['importer_slug']
#         file: file = request.FILES['file']

#         log.debug(f'Getting file: {file.name}')

#         if form.is_valid():
#             import_file = ImportFile(name=file.name, import_scheme=import_scheme)
#             import_file.save()
#             log.debug(f'Stored ImportFile with PKey of {import_file.id}')

#             log.debug(f'Getting ready to store file at: {settings.WORKING_FILES_DIR}{import_file.file_name}')
#             with open(settings.WORKING_FILES_DIR + import_file.file_name, 'wb+') as destination:
#                 for chunk in file.chunks():
#                     destination.write(chunk)

#             log.debug('Reverse URL after file save: ' + reverse('import_wizard:do_import', kwargs={'import_scheme_id': import_scheme.id}))
            
#             return JsonResponse({
#                 'redirect_url': reverse('import_wizard:do_import', kwargs={'import_scheme_id': import_scheme.id})
#             })

#         else:
#             # Needs to have a better error
#             return HttpResponseRedirect(reverse('import_wizard:import'))


class DoImport(View):
    ''' Do the actual import stuff '''

    def get(self, request, *args, **kwargs):
        ''' Do the actual import stuff '''
        import_scheme_id: int = kwargs.get('import_scheme_id', request.session.get('current_import_scheme_id'))
        log.debug(f'This is my import_scheme_id:{import_scheme_id}')

        # Return the user to the /import page if they don't have a valid import_scheme_id to work on
        if import_scheme_id is None:
            log.debug('Got bad import_scheme_id')
            return HttpResponseRedirect(reverse('import_wizard:import'))

        try:
            import_scheme: ImportScheme = ImportScheme.objects.get(pk=import_scheme_id)
        except ImportScheme.DoesNotExist:
            # Return the user to the /import page if they don't have a valid import_scheme to work on
            return HttpResponseRedirect(reverse('import_wizard:import'))
        
        request.session['current_import_scheme_id'] = import_scheme_id
        return render(request, 'do_import.django-html', {'importer': import_scheme.importer})