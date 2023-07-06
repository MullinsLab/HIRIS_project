from django import forms
from django.db.models import QuerySet

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import InlineRadios

from hiris.apps.core.models import DataSet


class DataSetPublicForm(forms.Form):
    """ Form to make a data set public """

    def __init__(self, *args, data_sets: QuerySet[DataSet], **kwargs):
        """ Create a field for each data set """

        super().__init__(*args, **kwargs)
        
        field_list: list = []

        for data_set in data_sets:
            field_name = f"is_public_{data_set.data_set_id}"
            initial: str = "public" if data_set.is_public else "everyone"

            self.fields[field_name] = forms.ChoiceField(
                choices=(("public", "Public"), ("everyone", "All registered users")), 
                required=True, 
                widget=forms.RadioSelect(),
                label=data_set.name,
                initial=initial,
            )

            field_list.append(InlineRadios(field_name))

        self.helper = FormHelper(*args, **kwargs)
        self.helper.form_id = f"data_set_public_{data_set.data_set_id}"
        # self.helper.form_class = 'blueForms'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            *field_list
        )