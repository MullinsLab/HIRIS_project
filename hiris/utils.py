""" Holds utility functions that are needed across the project """

import logging
logger = logging.getLogger("app")

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import reverse


class StaffRequiredMixin(LoginRequiredMixin):
    """Verify that the current user is authenticated and is staff."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user:
            return self.handle_no_permission()
        
        elif not request.user.is_staff:
            return HttpResponseRedirect(reverse("error_staff_required"))
        
        return super().dispatch(request, *args, **kwargs)