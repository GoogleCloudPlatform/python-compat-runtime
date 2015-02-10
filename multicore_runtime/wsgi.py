# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Configure a user project and instantiate WSGI app meta_app to serve it.

Importing this module will result in side-effects, such as registering the
project's default ticket via vmstub.Register. This is a straightforward and
compatible way to induce the webserver to run initialization code before
starting to serve the WSGI app.
"""

import logging

from dispatcher import dispatcher
from wsgi_utils import get_module_config
from wsgi_utils import get_module_config_filename
from wsgi_utils import load_user_scripts_into_handlers

from google.appengine.ext.vmruntime import vmconfig
from google.appengine.ext.vmruntime import vmstub


logging.basicConfig(level=logging.INFO)

appinfo_external = get_module_config(get_module_config_filename())
appengine_config = vmconfig.BuildVmAppengineEnvConfig()

# Ensure API requests include a valid ticket by default.
vmstub.Register(vmstub.VMStub(appengine_config.default_ticket))

# Load user code
preloaded_handlers = load_user_scripts_into_handlers(appinfo_external.handlers)

# Now that all scripts are fully imported, it is safe to use asynchronous
# API calls.
# TODO(apphosting): change this to use an env variable instead of module state
vmstub.app_is_loaded = True

# Create a "meta app" that dispatches requests based on handlers.
meta_app = dispatcher(preloaded_handlers)
