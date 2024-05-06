import logging
log = logging.getLogger("app")

from django_filters import filters
from django.contrib.auth.models import User

from rest_framework_datatables.django_filters.filters import GlobalFilter
from rest_framework_datatables.django_filters.filterset import DatatablesFilterSet

from hiris.apps.core.models import DataSet


class GlobalCharFilter(GlobalFilter, filters.CharFilter):
    pass


class UserGlobalFilter(DatatablesFilterSet):
    """ Filter name, username, and email with icontains """

    first_name = GlobalCharFilter(lookup_expr="icontains")
    last_name = GlobalCharFilter(lookup_expr="icontains")
    username = GlobalCharFilter(lookup_expr="icontains")
    email = GlobalCharFilter(lookup_expr="icontains")
    groups = GlobalCharFilter(field_name="groups__name", lookup_expr="icontains")

    class Meta:
        model = User
        fields = '__all__'


class DataSetFilter(DatatablesFilterSet):
    """ Filter DataSet by name and description """

    data_set_name = GlobalCharFilter(lookup_expr="icontains")

    class Meta:
        model = DataSet
        fields = '__all__'