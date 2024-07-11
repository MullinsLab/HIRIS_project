import logging
log = logging.getLogger('app')

import mimetypes

from django.views.generic.base import View
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import QuerySet
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User

from ml_export_wizard.utils.exporter import exporters, ExporterQuery

from hiris.apps.core import models
from hiris.apps.core.utils import db
from hiris.apps.core.utils.simple import underscore_keys, group_dict_list
from hiris.apps.core.utils.files import integrations_bed, integration_gene_summary_gff3


class Home(View):
    ''' The default view for HIRIS Home.  Currently shows the About page '''
    
    def get(self, request, *args, **kwargs) -> HttpResponse:
        ''' Returns the default template on a get '''

        summary_by_gene_top_12: list = db.get_summary_by_gene(limit=12, order_output=True, data_set_limit=request.session.get("data_set_limit", []))
        

        return render(request, "about.html", context={"summary_by_gene_top_12": summary_by_gene_top_12})

    def post(self, request, *args, **kwargs) -> HttpResponse:
        ''' Recieves the username and password for login '''
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)

        return render(request, "about.html")
    

class DataSources(View):
    """ View to show the data sources in the database """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """ Show the page """

        counts: dict = underscore_keys(db.get_environments_count())
        data_sources: dict = underscore_keys(group_dict_list(dict_list=db.get_data_sources(), key="integration_environment_name"))
        gene_count: int = db.get_genes_count()

        return render(request, "data_sources.html", context={"counts": counts, "gene_count": gene_count, "data_sources": data_sources})
    

class SummaryByGeneJS(View):
    """ The JS file that holds the data for gene summaries """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """ return the file """

        summary_by_gene: list = db.get_summary_by_gene(limit=12, order_output=True, data_set_limit=request.session.get("data_set_limit", []))

        return render(request, "summary-by-gene.js", context={"summary": summary_by_gene}, content_type="text/javascript")
    

class FullSummaryByGeneJS(View):
    """ The JS file that holds the data for full gene summaries """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """ return the file """

        summary_by_gene: list = db.get_summary_by_gene(order_output=True, data_set_limit=request.session.get("data_set_limit", []))

        return render(request, "summary-by-gene.js", context={"summary": summary_by_gene}, content_type="text/javascript")
    

class TopGenes(View):
    """ Stuff for the top_genes page """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """ The basic page """

        return render(request, "top_genes.html")
    

class GetTheData(View):
    """ Stuff for the get_the_data page """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """ The basic page """

        return render(request, "get_the_data.html")
    

class Exports(View):
    """ Class that serves files created from queries """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """ Return a file """

        file_name: str = kwargs['file_name'].split(".")[0]
        file_extension: str = kwargs['file_name'].split(".")[1]
        file_mime_type: str = mimetypes.guess_type(kwargs['file_name'])[0]
        query: ExporterQuery = None

        if file_extension == "gff3":
            file_content = integration_gene_summary_gff3(gene=file_name)
            file_mime_type = "text/plain"
            
        elif file_mime_type:
            match file_name:
                case "integration-summary":
                    query = exporters["IntegrationsSummary"].query()
                case "integration-gene-summary":
                    query = exporters["IntegrationsGeneSummary"].query()
                case "summary-by-gene":
                    query = exporters["SummaryByGene"].query()

            # Query stuff to limit data sets by user/group
            query.external_values = db.get_current_user_external_value()

            # Query stuff to limit data sets acording to the session
            query.where_before_join = {
                "DataSet": [{
                    "field": "data_set_id",
                    "value": request.session.get("data_set_limit", list(models.DataSet.objects.all().values_list('pk', flat=True))),
                    "operator": "in",
                }],
            }

            match file_mime_type:
                case "text/csv":
                    file_content = query.csv()
                case "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                    file_content = query.xlsx()
                case "application/json":
                    file_content = query.json()
                case "application/vnd.realvnc.bed":
                    file_content = integrations_bed(environment=file_name.replace("_", " "))

        return HttpResponse(file_content, content_type=file_mime_type)


class ListGFFs(LoginRequiredMixin, View):
    """ Lists all the GFF files that can be created from database """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """ The basic page """
        
        genes: list[str] = db.genes_with_integrations()

        return render(request, "list_gffs.html", context={"genes": genes})
    

# Views for managing data
class DataTools(LoginRequiredMixin, View):
    """ List of the tools for managing data """

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """ The basic page """

        return render(request, "tools.html")