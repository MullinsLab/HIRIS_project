import logging
log = logging.getLogger('app')


from django import forms

from django.contrib.auth.models import User, Group


class UserForm(forms.ModelForm):
    """ Form for creating/editing a scientist. """

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "groups")
        widgets = {"groups": forms.CheckboxSelectMultiple()}


class UserPasswordForm(forms.Form):
    """ Form for setting a user's password. """

    user_id = forms.IntegerField(widget=forms.HiddenInput())
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        """ Ensure the passwords match. """
        
        cleaned_data = super().clean()

        if cleaned_data.get("password") != cleaned_data.get("password_confirm"):
            self.add_error(None, "Passwords did not match.")
        
        return cleaned_data
    
    def save(self, commit=True):
        """ Update the password. """

        user: User = User.objects.get(pk=self.cleaned_data["user_id"])
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user
    

class GroupForm(forms.ModelForm):
    """ Form for creating/editing a group. """

    class Meta:
        model = Group
        fields = ("name",)