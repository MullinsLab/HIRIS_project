import logging
log = logging.getLogger('app')


from django import forms

from django.contrib.auth.models import User, Group


class UserForm(forms.ModelForm):
    """ Form for creating/editing a scientist. """

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "groups")
        widgets = {
        #     "name": forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 50em;'}),
        #     "email": forms.TextInput(attrs={'placeholder': 'Email', 'style': 'width: 50em;'}),
        #     "lab": forms.Select(),
            "groups": forms.CheckboxSelectMultiple()
        }

    # def __init__(self, *args, **kwargs) -> None:
    #     super().__init__(*args, **kwargs)
    #     self.fields["scientist_group"].queryset = ScientistGroup.objects.filter(display=True).order_by('name')

    # def save(self, commit=True):
    #     """ Save the scientist, and update the info on the Django user, if it exists """

    #     old_email: str = None
    #     if not self.instance._state.adding:
    #         old_email = Scientist.objects.get(pk=self.instance.pk).email
        
    #     scientist: Scientist = super().save(commit=commit)

    #     try:
    #         if old_email:
    #             user: User = User.objects.get(email=old_email)
    #             user.email = scientist.email
    #             user.username = scientist.email
    #             user.save()

    #     except User.DoesNotExist:
    #         pass

    #     return scientist