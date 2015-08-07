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
project's default ticket via vmstub.Register. This is a broadly compatible way
to induce the webserver to run initialization code before starting to serve the
WSGI app.
"""

import logging
import os

import cloud_logging
from dispatcher import dispatcher
from middleware import health_check_middleware
from middleware import reset_environment_middleware
from wsgi_config import env_vars_from_env_config
from wsgi_config import get_module_config
from wsgi_config import get_module_config_filename
from wsgi_config import load_user_scripts_into_handlers
from wsgi_config import ThreadLocalDict
from wsgi_config import user_env_vars_from_appinfo

from google.appengine.ext.vmruntime import vmconfig
from google.appengine.ext.vmruntime import vmstub

# Configure logging to output structured JSON to Cloud Logging.
root_logger = logging.getLogger('')
try:
  handler = cloud_logging.CloudLoggingHandler()
  root_logger.addHandler(handler)
except IOError:
  # If the Cloud Logging endpoint does not exist, just use the default handler
  # instead. This will be the case when running in local dev mode.
  pass

root_logger.setLevel(logging.INFO)

# Fetch application configuration via the config file.
appinfo = get_module_config(get_module_config_filename())
env_config = vmconfig.BuildVmAppengineEnvConfig()

# Ensure API requests include a valid ticket by default.
vmstub.Register(vmstub.VMStub(env_config.default_ticket))

# Take an immutable snapshot of env data from env_config. This is added to the
# environment in `reset_environment_middleware` in a particular order to ensure
# that it cannot be overridden by other steps.
frozen_env_config_env = tuple(
    env_vars_from_env_config(env_config).iteritems())

# Also freeze user env vars specified in app.yaml. Later steps to modify the
# environment such as env_vars_from_env_config and request middleware
# will overwrite these changes. This is added to the environment in
# `reset_environment_middleware`.
frozen_user_env = tuple(
    user_env_vars_from_appinfo(appinfo).iteritems())

# While the primary use of the frozen env vars is for
# `reset_environment_middleware`, we'll also add them to the env here to make
# them available during app preloading. This is useful for apps which have
# side-effects at import time (which is not recommended).
os.environ.update(frozen_user_env)
os.environ.update(frozen_env_config_env)

# Decide whether to enable support for legacy end-to-end tests. This is intended
# to be temporary.
# TODO(apphosting): Modify the end-to-end test runner to make this step
# unnecessary.
legacy_e2e_support = appinfo.vm_settings.get('vm_runtime') == 'python'

# Load user code.
if legacy_e2e_support:
  import legacy_e2e_support  # pylint: disable=g-import-not-at-top
  preloaded_handlers = legacy_e2e_support.load_legacy_scripts_into_handlers(
      appinfo.handlers)
else:
  preloaded_handlers = load_user_scripts_into_handlers(appinfo.handlers)

# Now that all scripts are fully imported, it is safe to use asynchronous
# API calls.
# TODO(apphosting): change this to use an env variable instead of module state
vmstub.app_is_loaded = True

# Take an immutable snapshot of the environment's current state, which we will
# use to refresh the environment (via `reset_environment_middleware`) at the
# beginning of each request.
# It would be cleaner to take this snapshot earlier in the process, but app
# preloading may trigger any arbitrary user code, including code that modifies
# the environment, and we need to capture any results from that.
frozen_environment = tuple(os.environ.iteritems())

# Monkey-patch os.environ to be thread-local. This is for backwards
# compatibility with GAE's use of environment variables to store request data.
# Note: gunicorn "gevent" or "eventlet" workers, if selected, will
# automatically monkey-patch the threading module to make this work with green
# threads.
os.environ = ThreadLocalDict()

# Create a "meta app" that dispatches requests based on handlers.
meta_app = dispatcher(preloaded_handlers)

# Wrap meta_app in middleware. The first statement in this section is the
# innermost layer of the middleware, and the last statement is the outermost
# layer (the middleware code that will process a request first). Inside the
# innermost layer is the actual dispatcher, above.

# Intercept health check requests on /_ah/health. This is a temporary measure
# until container-level health check handlers are in place and turned on.
meta_app = health_check_middleware(meta_app)

# Reset os.environ to the frozen state and add request-specific data.
meta_app = reset_environment_middleware(meta_app, frozen_environment,
                                        frozen_user_env,
                                        frozen_env_config_env)
