from django.conf import settings
from django.urls import resolve

import logging
log = logging.getLogger('app')


class AddHTTP_X_FORWARDED_PORTMiddleware:
    def __init__(self, get_response):
        """ Get the get_response function and store it for later"""

        self.get_response = get_response

    def __call__(self, request):
        """ Add the HTTP_X_FORWARDED_PORT header and return the response """
        
        # Only inject the port number for saml pages
        if resolve(request.path_info).url_name in ("saml_login", "saml_sso"):
            request.META["HTTP_X_FORWARDED_PORT"] = settings.EXTERNAL_WEB_PORT

        return self.get_response(request)