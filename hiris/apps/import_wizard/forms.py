from django import forms
# from crispy_forms.helper import FormHelper

class UploadFileForImport(forms.Form):
    ''' Get a file to start importing from '''
    file = forms.FileField()

    # def __init__(self, *args, **kwargs):
    #     ''' Override the parent's init to include the forms helper'''
    #     super().__init__(*args, **kwargs)

    #     self.helper = FormHelper()
    #     self.helper.form_id = 'upload_file_for_import'
    #     self.helper.form_class = 'blueForms'
    #     self.helper.form_method = 'post'
    #     # self.helper.form_action = 'submit_survey'

    #     self.helper.add_input(Submit('submit', 'Submit'))