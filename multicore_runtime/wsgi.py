import logging
import re
import sys

from google.appengine.ext.vmruntime import vmstub
from google.appengine.ext.vmruntime import vmconfig

from dispatcher import dispatcher
from wsgi_utils import get_module_config
from wsgi_utils import get_module_config_filename
from wsgi_utils import load_user_scripts_into_handlers

logging.basicConfig(level=logging.INFO)

appinfo_external = get_module_config(get_module_config_filename())
appengine_config = vmconfig.BuildVmAppengineEnvConfig()

# Ensure API requests include a valid ticket by default.
vmstub.Register(vmstub.VMStub(appengine_config.default_ticket))

# Load user code
preloaded_handlers = load_user_scripts_into_handlers(appinfo_external.handlers)

# Now that all scripts are fully imported, it is safe to use asynchronous
# API calls.
# TODO: change this to use an env variable instead of module state
vmstub.app_is_loaded = True

# Create a "meta app" that dispatches requests based on handlers.
meta_app = dispatcher(preloaded_handlers)
