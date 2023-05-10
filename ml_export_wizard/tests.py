from django.test import TestCase
from django.conf import settings

import logging
log = logging.getLogger('test')



class InclusionTest(TestCase):
    """ A test to make sure the Import Wizard app is being included """

    def test_true_is_true(self):
        """ Make sure True is True """
        self.assertTrue(True)

    def test_setting_dict_exists(self):
        """ Test that there is something in the ML_EXPORT_WIZARD setting. """
        self.assertIs(type(settings.ML_EXPORT_WIZARD), dict)