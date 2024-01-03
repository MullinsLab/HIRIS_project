### Settings for the HiRIS app

import os, sys
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Needed to find ml_import_wizard.  Remove if it's ever installed as a package.
if os.path.exists(os.path.join(BASE_DIR, 'ML_Import_Wizard')):
    sys.path.insert(0, os.path.join(BASE_DIR, 'ML_Import_Wizard'))

# Take environment variables from .env file
# env = environ.Env(DEBUG=(int, 0))
# environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

from .base_settings import *       # All Django related settings
from .third_party_settings import *  # UW-SAML2
from .importer_settings import *
from .exporter_settings import *
