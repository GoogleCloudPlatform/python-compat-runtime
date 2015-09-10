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
"""WSGI middleware to wrap the dispatcher, and supporting functions."""

import httplib
import logging
import os

from werkzeug import wrappers


# A dict of reserved env keys; the value is used as the default if not
# otherwise set.
RESERVED_ENV_KEYS = {
    'AUTH_DOMAIN': 'gmail.com',  # Default auth domain must be set.
    'DATACENTER': '',
    'DEFAULT_VERSION_HOSTNAME': '',
    'HTTPS': '',
    'REMOTE_ADDR': '',
    'REQUEST_ID_HASH': '',
    'REQUEST_LOG_ID': '',
    'USER_EMAIL': '',
    'USER_ID': '',
    'USER_IS_ADMIN': '0',  # Default admin flag to explicit '0'.
    'USER_NICKNAME': '',
    'USER_ORGANIZATION': '',
    }


def reset_environment_middleware(app, frozen_environment, frozen_user_env,
                                 frozen_env_config_env):
  """Replace the contents of os.environ with a frozen env + request data.

  This requires a single-threaded webserver, or for os.environ to be patched to
  be thread-local.

  Args:
    app: The WSGI app to wrap.
    frozen_environment: An iterable of (key, value) tuples that can be used to
      populate os.environ with the initial state of the environment.
      `tuple(os.environ.iteritems())` produces appropriate output.
    frozen_user_env: An iterable of (key, value) tuples that can be used to
      populate os.environ with environment variables specified in app.yaml.
    frozen_env_config_env: An iterable of (key, value) tuples that can be
      used to populate os.environ with configuration-dependent env variables.

  Returns:
    The wrapped app, also a WSGI app.
  """

  @wrappers.Request.application
  def reset_environment_wrapper(request):
    """Reset the system environment and populate it with wsgi_env."""
    # Wipe os.environ entirely.
    os.environ.clear()

    # Populate os.environ in order, so that later steps overwrite conflicting
    # keys in previous steps.

    # Add in user env variables specified in app.yaml. These are added first
    # because they should not take precedence over any conflicting key.
    os.environ.update(frozen_user_env)

    # Repopulate os.environ with the frozen environment.
    os.environ.update(frozen_environment)

    # Add in wsgi_env data, including request headers.
    os.environ.update(request_environment_for_wsgi_env(request.environ))

    # Add in configuration data from env_config.
    os.environ.update(frozen_env_config_env)

    # Add reserved keys, which draw from wsgi_env as well. These have a very
    # high priority and so are added nearly last.
    os.environ.update(reserved_env_keys_for_wsgi_env(request.environ))

    # Tweak the environment to hide the service bridge.
    os.environ.update(get_env_to_hide_service_bridge(request.environ))

    return app

  return reset_environment_wrapper


def request_environment_for_wsgi_env(wsgi_env):
  """Get a dict of key-value pairs from wsgi_env that work as env variables.

  Does not mutate input.

  Args:
    wsgi_env: WSGI request env data.

  Returns:
    A dictionary suitable for use in `os.environ.update(output)`.
  """

  # Return all key, value pairs from wsgi_env where value is a string.
  return {key: value for key, value in wsgi_env.iteritems()
          if isinstance(value, basestring)}


def reserved_env_keys_for_wsgi_env(wsgi_env):
  """Get a dict for reserved keys based on wsgi_env headers and defaults.

  Does not mutate input.

  Args:
    wsgi_env: WSGI request env data.

  Returns:
    A dictionary suitable for use in `os.environ.update(output)`.
  """

  output = {}

  # Use the default value for a reserved key if the corresponding header is not
  # set, or if the header exists but its value is blank.
  for key, default in RESERVED_ENV_KEYS.iteritems():
    value = wsgi_env.get('HTTP_X_APPENGINE_{key}'.format(key=key))
    output[key] = value or default  # Must be set to a valid value or default.

  return output


def get_env_to_hide_service_bridge(wsgi_env):
  """Generate a dictionary of environment variables to hide the service bridge.

  Does not mutate input.

  Args:
    wsgi_env: WSGI request env data.

  Returns:
    A dictionary suitable for use in `os.environ.update(output)`.
  """
  output = {}

  # Because the request is coming over the service bridge, the service bridge
  # host and port that are automatically populated in SERVER_NAME and
  # SERVER_PORT, respectively.  However, this is an implementation detail that
  # should not be shown to user code. Instead, we'll rely on the HTTP Host
  # header to retrieve the hostname used in the original request.  This mimics
  # the behavior of non-VM App Engine.
  http_host = wsgi_env.get('HTTP_HOST', None)
  if http_host:
    output['SERVER_NAME'] = http_host

  # Similarly we'll use the HTTPS flag to determine the port used in the
  # original request.
  https = wsgi_env.get('HTTP_X_APPENGINE_HTTPS', 'off')
  if https == 'off':
    output['SERVER_PORT'] = '80'
  elif https == 'on':
    output['SERVER_PORT'] = '443'
  else:
    logging.warning(
        'Unrecognized value for HTTPS (%s), won\'t modify SERVER_PORT', https)

  return output


def health_check_middleware(app):
  """Intercept requests to /_ah/health and respond healthy (200 OK).

  Args:
    app: The WSGI app to wrap.

  Returns:
    The wrapped app, also a WSGI app.
  """

  @wrappers.Request.application
  def health_check_intercept_wrapper(request):
    """Capture a request to /_ah/health and respond with 200 OK."""
    if request.path == '/_ah/health':  # Only intercept exact matches.
      return wrappers.Response('healthy', status=httplib.OK)
    else:
      return app

  return health_check_intercept_wrapper
