""" Holds utility functions that are needed across the project """

import logging
logger = logging.getLogger("app")

from functools import cache

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect
from django.shortcuts import reverse

from hiris.utils_early import get_request_object


class StaffRequiredMixin(LoginRequiredMixin):
    """Verify that the current user is authenticated and is staff."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user:
            return self.handle_no_permission()
        
        elif not request.user.is_staff:
            return HttpResponseRedirect(reverse("error_staff_required"))
        
        return super().dispatch(request, *args, **kwargs)
    

@cache
def get_anonymous_user():
    """ Returns the anonymout user """

    return User.objects.get(username="AnonymousUser")


@cache
def get_everyone_group():
    """ Returns the everyone group """

    return Group.objects.get(name="Everyone")


def current_user():
    request = get_request_object()

    if isinstance(request.user, AnonymousUser):
        return get_anonymous_user()

    return request.user