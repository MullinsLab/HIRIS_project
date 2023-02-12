from django.test import TestCase

class TempTest(TestCase):
    ''' A test to make sure the import app is being included '''
    def test_true_is_true(self):
        ''' Makesure True is True '''
        self.assertTrue(True)