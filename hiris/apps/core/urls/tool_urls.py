from django.contrib.auth.decorators import login_required
from django.urls import path, include

import logging
log = logging.getLogger('app')

from hiris.apps.core import views

# determine appname
app_name='tools'

urlpatterns = [
    path('', views.Home.as_view(), name='about'),
    path('datasources', views.DataSources.as_view(), name='data_sources'),
    path('top_genes', views.TopGenes.as_view(), name='top_genes'),
    path('get_the_data', views.GetTheData.as_view(), name='get_the_data'),
    path("exports/<str:file_name>", views.Exports.as_view(), name="exports"),
    path("summary-by-gene.js", views.SummaryByGeneJS.as_view(), name="summary_by_gene_js"),
    path("full-summary-by-gene.js", views.FullSummaryByGeneJS.as_view(), name="full_summary_by_gene_js"),
    path ("list_gffs", views.ListGFFs.as_view(), name="gff_files"),
    path("data_tools", views.DataTools.as_view(), name="data_tools"),
    # path("data_access", views.DataAccess.as_view(), name="data_access"),
]
