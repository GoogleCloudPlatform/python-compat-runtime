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
"""Utilities to configure the dispatcher, middleware and environment."""

import logging
import os
import threading
import UserDict

from . import static_files

from google.appengine.api import appinfo
from google.appengine.api import appinfo_includes
from google.appengine.runtime import wsgi


def get_module_config_filename():
  """Returns the path of the module configuration file (e.g. 'app.yaml').

  Returns:
    The path of the module configuration file.

  Raises:
    KeyError: The MODULE_YAML_PATH environment variable is not set.
  """
  module_yaml_path = os.environ['MODULE_YAML_PATH']
  logging.info('Using module_yaml_path from env: %s', module_yaml_path)
  return module_yaml_path


def get_module_config(filename):
  """Returns the parsed module config."""
  with open(filename) as f:
    return appinfo_includes.Parse(f)


def app_for_script(script):
  """Returns the WSGI app specified in the input string, or None on failure."""
  try:
    app, unused_filename, err = wsgi.LoadObject(script)
    if err:  # wsgi.LoadObject guarantees this is either None or ImportError.
      raise err
  except ImportError:
    # Despite returning an error object sometimes, LoadObject will other times
    # just raise an exception. By raising the err object if it exists, we
    # catch either.
    logging.exception('Failed to import %s', script)
    return None
  else:
    return app_wrapped_in_user_middleware(app)


def app_wrapped_in_user_middleware(app):
  """Returns the input WSGI app, wrapped in appengine_config middleware."""
  add_middleware = get_add_middleware_from_appengine_config()
  if add_middleware:
    return add_middleware(app)
  else:
    return app


def get_add_middleware_from_appengine_config():
  """Tries to import appengine_config and return middleware; fails silently.

  `env_config` is optionally part of GAE-compatible user code.
  If the user chooses to define the `webapp_add_wsgi_middleware` function
  there, then we will use it to wrap app scripts. This is used for e.g.
  appstats. Many user apps do not have or need env_config, so failure
  to import it or failure to find `webapp_add_wsgi_middleware` is not an
  error.

  Returns:
    The appengine_config.webapp_add_wsgi_middleware function or None.
  """
  try:
    import appengine_config  # pylint: disable=g-import-not-at-top
    return getattr(appengine_config, 'webapp_add_wsgi_middleware', None)
  except ImportError:
    return None


def static_app_for_handler(handler):
  """Returns a WSGI app that serves static files as directed by the handler.

  Args:
    handler: An individual handler from appinfo_external.handlers
      (appinfo.URLMap)

  Returns:
    A static file-serving WSGI app closed over the handler information.
  """
  url_re = handler.url  # handler.url is a regex, despite the name.
  files = handler.static_files
  upload_re = handler.upload
  if not files:
    if handler.static_dir:
      # If static_files is not set, convert static_dir to static_files and also
      # modify the url regex accordingly. See the appinfo.URLMap docstring for
      # more information.
      url_re = static_dir_url_re(handler)
      files = r'{dir}/\1'.format(dir=handler.static_dir)
      upload_re = '{dir}/.*'.format(dir=handler.static_dir)
    else:
      # Neither static_files nor static_dir is set; log an error and return.
      logging.error('No script, static_files or static_dir found for %s',
                    handler)
      return None
  return static_files.static_app_for_regex_and_files(
      url_re, files, upload_re, mime_type=handler.mime_type)


def static_dir_url_re(handler):
  """Converts a static_dir regex into a static_files regex if needed.

  See the appinfo.URLMap docstring for more information.

  Args:
    handler: A handler (appinfo.URLMap)

  Returns:
    A modified url regex
  """
  if not handler.script and not handler.static_files and handler.static_dir:
    return '{url_re}/(.*)'.format(url_re=handler.url)
  else:
    return handler.url


def load_user_scripts_into_handlers(handlers):
  """Preloads user scripts, wrapped in env_config middleware if present.

  Args:
    handlers: appinfo.handlers data as provided by get_module_config()

  Returns:
    A list of tuples suitable for configuring the dispatcher() app,
    where the tuples are (url, app):
      - url_re: The url regular expression which matches this handler.
      - app: The fully loaded app corresponding to the script.
  """
  # `if handler.login == appinfo.LOGIN_OPTIONAL` disables loading handlers
  # that require login or admin status entirely. This is a temporary
  # measure until handling of login-required handlers is implemented
  # securely.
  loaded_handlers = []
  for handler in handlers:
    if handler.login == appinfo.LOGIN_OPTIONAL:
      if handler.script:  # An application, not a static files directive.
        url_re = handler.url
        app = app_for_script(handler.script)
      else:  # A static files directive, either with static_files or static_dir.
        if handler.static_files:
          url_re = handler.url
        else:  # This is a "static_dir" directive.
          url_re = static_dir_url_re(handler)
        app = static_app_for_handler(handler)
      loaded_handlers.append((url_re, app))
  logging.info('Parsed handlers: %r',
               [url_re for (url_re, _) in loaded_handlers])
  return loaded_handlers


def env_vars_from_env_config(env_config):
  """Generate a dict suitable for updating os.environ to reflect app config.

  This function only returns a dict and does not update os.environ directly.

  Args:
    env_config: The app configuration as generated by
                vmconfig.BuildVmAppengineEnvConfig()

  Returns:
    A dict of strings suitable for e.g. `os.environ.update(values)`.
  """

  return {
      'SERVER_SOFTWARE': env_config.server_software,
      'APPENGINE_RUNTIME': 'python27',
      'APPLICATION_ID': '%s~%s' % (env_config.partition,
                                   env_config.appid),
      'INSTANCE_ID': env_config.instance,
      'BACKEND_ID': env_config.major_version,
      'CURRENT_MODULE_ID': env_config.module,
      'CURRENT_VERSION_ID': '%s.%s' % (env_config.major_version,
                                       env_config.minor_version),
      'DEFAULT_TICKET': env_config.default_ticket,
      }


def user_env_vars_from_appinfo(appinfo_ext):
  """Generate a dict of env variables specified by the user in app.yaml.

  This function only returns a dict and does not update os.environ directly.

  Args:
    appinfo_ext: The configuration info (a parsed yaml object) as generated by
                 get_module_config()

  Returns:
    A dict of strings suitable for e.g. `os.environ.update(values)`.
  """

  return appinfo_ext.env_variables or {}


class ThreadLocalDict(UserDict.IterableUserDict, threading.local):
  """A dictionary with thread-local contents."""
