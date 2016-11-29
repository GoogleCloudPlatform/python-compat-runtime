#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
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




"""Tools for WSGI applications that dispatch based on an app.yaml."""

from __future__ import with_statement

import logging
import logging.handlers
import mimetypes
import os
import re
import runpy
import sys
import threading
import time
import urlparse
from wsgiref import handlers

import requests

from google.appengine.api import appinfo
from google.appengine.api import appinfo_includes


from google.appengine.api.runtime import runtime

from google.appengine.ext.vmruntime import middlewares
from google.appengine.ext.vmruntime import vmstub
from google.appengine.ext.webapp import util as webapp_util

from google.appengine.runtime import wsgi

try:
  import webapp2
except ImportError:

  from google.third_party.apphosting.python.webapp2.v2_3 import webapp2


class Error(Exception):
  pass


class AppLoadError(Error):
  """Could not load the user's app into our meta app."""
  pass


def FullyWrappedAppFromYAML(filename, appengine_config):
  """Like FullyWrappedApp, but first arg is a file name containing YAML."""
  with open(filename) as stream:
    appinfo_external = appinfo_includes.Parse(stream)
  return FullyWrappedApp(appinfo_external, appengine_config)


def FullyWrappedApp(appinfo_external, appengine_config):
  """Completely wraps a user's app per the given YAML file.

  Should only be called once per process. Note that any file referenced in the
  imports of appinfo_external should be written to disk at the corresponding
  relative path.

  Args:
    appinfo_external: an AppInfoExternal for this app, usually (always?) parsed
      from an app.yaml.
    appengine_config: A VmAppengineEnvConfig object.

  Returns:
    A WSGI app, properly scaffolded for the GAE VM runtime.
  """
  app = MetaWSGIApp(appinfo_external, appengine_config)
  app = middlewares.RequestLoggingMiddleware(app)
  app = middlewares.ErrorLoggingMiddleware(app)
  app = middlewares.WsgiEnvSettingMiddleware(app, appinfo_external)
  app = middlewares.FixServerEnvVarsMiddleware(app)
  app = middlewares.OsEnvSetupMiddleware(app, appengine_config)


  app = middlewares.PatchLoggingMethods(app)
  app = middlewares.LogFlushCounter(app)
  app = middlewares.RequestQueueingMiddleware(app, appinfo_external)
  app = middlewares.UseRequestSecurityTicketForApiMiddleware(app)
  app = middlewares.CallbackMiddleware(app)
  return app


DEFAULT_DJANGO_VERSION = '1.4'
ENV_KEYS = [
    'AUTH_DOMAIN',
    'DATACENTER',
    'DEFAULT_VERSION_HOSTNAME',
    'HTTPS',
    'REMOTE_ADDR',
    'REQUEST_ID_HASH',
    'REQUEST_LOG_ID',
    'USER_EMAIL',
    'USER_ID',
    'USER_IS_ADMIN',
    'USER_NICKNAME',
    'USER_ORGANIZATION',
    ]



X_APPENGINE_USER_IP_ENV_KEY = 'HTTP_X_APPENGINE_USER_IP'

X_GOOGLE_REAL_IP_ENV_KEY = 'HTTP_X_GOOGLE_REAL_IP'

WSGI_REMOTE_ADDR_ENV_KEY = 'REMOTE_ADDR'



DEFAULT_HEALTH_CHECK_INTERVAL_SEC = 5
HEALTH_CHECK_INTERVAL_OFFSET_RATIO = 1.5


def _HandleShutdown():
  """Runs the user-provided GAE shutdown hook, if any."""


  logging.info('Shutdown request received.')
  runtime.__BeginShutdown()


def _QueryHealthCheckPath(app_health_check_path, headers):
  parsed_path = urlparse.urlparse(app_health_check_path)
  app_health_check_url = urlparse.urlunparse(
      ('http', '127.0.0.1:8080', parsed_path.path,
       parsed_path.params, parsed_path.query, parsed_path.fragment)
  )
  return requests.get(app_health_check_url, allow_redirects=False,
                      headers=headers)


class StopHandler(webapp2.RequestHandler):

  def get(self):
    _HandleShutdown()
    self.response.out.write('ok')


class HealthHandler(webapp2.RequestHandler):

  def get(self):
    expected_version = self.request.get('VersionID')
    actual_version = os.environ['CURRENT_VERSION_ID']


    if os.environ['CURRENT_MODULE_ID'] != 'default':
      actual_version = '%s:%s' % (os.environ['CURRENT_MODULE_ID'],
                                  actual_version)

    if expected_version == actual_version or not expected_version:
      self.response.headers['content-type'] = 'text/plain'
      self.response.out.write('ok')
    else:
      self.response.headers['content-type'] = 'text/plain'
      self.response.out.write('version mismatch "%s" != "%s"' %
                              (expected_version, actual_version))


internal_app = webapp2.WSGIApplication([
    ('/_ah/health', HealthHandler),
    ('/_ah/stop', StopHandler),
    ])


class _MockedWsgiHandler(object):
  """Mock for wsgiref.handler classes."""

  python_25_app_lock = threading.Lock()

  def __init__(self, app_holder):
    self._app_holder = app_holder

  def run(self, app):
    self._app_holder.append(app)


class _StubOut(object):
  """Object for setting and then easily removing stubs."""

  def __init__(self):

    self._stubs = {}

  def Set(self, obj, attr_string, new_attr):
    old_attr = getattr(obj, attr_string)
    self._stubs.setdefault((obj, attr_string), old_attr)
    setattr(obj, attr_string, new_attr)

  def CleanUp(self):
    for (obj, field_str), old_value in self._stubs.iteritems():
      setattr(obj, field_str, old_value)













def _StubWSGIUtils(output_app_holder):
  """Stub out WSGI adapters for python 2.5."""
  stubs = _StubOut()
  stubbed_wsgi_handler_class = (
      lambda * args, **kwargs: _MockedWsgiHandler(output_app_holder))

  def RunWSGIStub(application):
    output_app_holder.append(application)

  stubs.Set(webapp_util, 'run_bare_wsgi_app', RunWSGIStub)
  stubs.Set(webapp_util, 'run_wsgi_app', RunWSGIStub)



  stubs.Set(handlers, 'BaseHandler', stubbed_wsgi_handler_class)
  stubs.Set(handlers, 'SimpleHandler', stubbed_wsgi_handler_class)
  stubs.Set(handlers, 'BaseCGIHandler', stubbed_wsgi_handler_class)
  stubs.Set(handlers, 'CGIHandler', stubbed_wsgi_handler_class)


  return stubs.CleanUp


def _NormalizedScript(script):
  """Translates $PYTHON_LIB in the given script. Returns the translation."""
  if script:
    return script.replace('$PYTHON_LIB/', '')
  return script




def _AppFrom27StyleScript(script):
  """Returns application given a python2.7 app.yaml script specification.

  Args:
    script: A script specification from a python27 app.yaml. e.g. my.module.app

  Returns:
    (app, filename) The application as extracted from the script, and the name
    of the file containing the app.

  Raises:
    ImportError: If the given script specification is malformed.
  """
  app, filename, err = wsgi.LoadObject(script)
  if err:
    raise err
  return app, filename







def _AppFrom25StyleScript(script):
  """Returns application given a python2.5 app.yaml script specification.

  Args:
    script: A script specification from a python27 app.yaml. e.g. my.module.app

  Returns:
    (app, filename) The application as extracted from the script, and the name
    of the file containing the app.

  Raises:
    AppLoadError: If we couldn't load the user's app.
  """
  modname, _ = script.rsplit('.', 1)
  app_holder = []
  revert_func = lambda: None
  try:
    revert_func = _StubWSGIUtils(app_holder)
    mod_global_dict = runpy.run_module(modname, run_name='__main__')
  finally:
    revert_func()
  f = mod_global_dict['__file__']
  if app_holder:
    return app_holder[0], f
  else:
    raise AppLoadError('Cannot load an app from %s' % script)


class MetaWSGIApp(object):
  """A WSGI app that dispatches based on app.yaml.

  The app.yaml handlers must use Python 2.7 WSGI handlers.

  ATTRIBUTES:
    appinfo_external: The AppInfoExternal YAML object corresponding to the
      app_yaml_filename constructor parameter.
    threadsafe: Whether or not this app is threadsafe, per app.yaml.
    handlers: A list of tuples of (url, script, l7_safe, appinfo.URLMap).
    - url: The url pattern which matches this handler.
    - script: The script to serve for this handler.
    - l7_safe: Is this handler safe to serve from the l7lb. Only pages
      that don't have login requirements are safe for l7lb.
    - appinfo.URLMap: The full appinfo URLMap for this handler.
    The first three are contained in the fourth, but are unpacked for
    l7_unsafe_redirect_url: the base url to redirect unsafe l7 requests that
    did not come from the appserver via the service bridge.
  """

  def __init__(self, appinfo_external, appinfo_config):
    """Parse app.yaml file and extract valid handlers."""
    self.appinfo_external = appinfo_external
    self.threadsafe = appinfo_external.threadsafe
    self.handlers = [(x.url,
                      _NormalizedScript(x.script),
                      x.login == appinfo.LOGIN_OPTIONAL,
                      x)
                     for x in appinfo_external.handlers]
    logging.info('Parsed handlers: %s', [(x[0], x[1]) for x in self.handlers])
    sys.path[:] = FixDjangoPath(appinfo_external.libraries, sys.path)
    self.user_env_variables = appinfo_external.env_variables or {}
    self.l7_unsafe_redirect_url = 'https://%s-dot-%s-dot-%s' % (
        appinfo_config.major_version,
        appinfo_config.module,
        appinfo_config.appengine_hostname)


    self.is_last_successful = False
    self.is_last_successful_time = None
    if (self.appinfo_external.vm_health_check is None or
        self.appinfo_external.vm_health_check.check_interval_sec is None):
      self.check_interval_sec = DEFAULT_HEALTH_CHECK_INTERVAL_SEC
    else:
      vm_health_check = self.appinfo_external.vm_health_check
      self.check_interval_sec = vm_health_check.check_interval_sec

  def _CheckIsValidAddress(self, valid_networks, octets_to_match, address):
    """Check that an ip address is in valid_networks.

    Args:
      valid_networks: An iterable of valid ipv4 networks in string form.
      octets_to_match: The number of octets needed to match to be valid.
      address: The address to check.

    Returns:
      True iff the the addr is valid.
    """

    network = '.'.join(address.split('.')[:octets_to_match])
    return network in valid_networks

  def _CheckIsLocalAddress(self, address):
    local_ip_networks = (

        '127.0',

        '172.17')
    return self._CheckIsValidAddress(local_ip_networks, 2, address)

  def _CheckIsTrustedIpAddress(self, address):
    """Check if the given ip address came from appserver or localhost."""
    valid_ip_networks = (

        '169.254',

        '192.168')
    if address == '10.0.2.2':






      return True
    return (self._CheckIsValidAddress(valid_ip_networks, 2, address) or
            self._CheckIsLocalAddress(address))

  def _CheckIsValidHealthCheckAddress(self, address):
    """Check if the given remote address came from a valid health check ip."""

    valid_ip_networks = ('130.211.0', '130.211.1', '130.211.2', '130.211.3')
    return (self._CheckIsTrustedIpAddress(address) or
            self._CheckIsValidAddress(valid_ip_networks, 3, address))

  def GetUserApp(self, script):
    """Extracts the user's app given a script specification."""


    vm_runtime = self.appinfo_external.vm_settings.get('vm_runtime')
    if vm_runtime in ['python27', 'custom']:
      app = _AppFrom27StyleScript(script)
    elif vm_runtime == 'python':
      with _MockedWsgiHandler.python_25_app_lock:
        app = _AppFrom25StyleScript(script)
    else:
      raise ValueError('Unexpected runtime: %s' % vm_runtime)


    vmstub.app_is_loaded = True

    return app



  def __call__(self, env, start_response):
    """Handle one request."""


    remote_addr = (env.get(X_GOOGLE_REAL_IP_ENV_KEY, '') or
                   env.get(WSGI_REMOTE_ADDR_ENV_KEY, ''))
    path = env['PATH_INFO']
    if path == '/_ah/stop':


      return self.ServeApp(internal_app, 'internal', env, start_response)

    if path == '/_ah/health':
      if not self._CheckIsValidHealthCheckAddress(remote_addr):
        logging.error('Invalid health check address %s, aborting request!',
                      remote_addr)
        start_response('403 Forbidden', [])
        return ['<h1>403 Forbidden</h1>\n']
      return self.ServeHealthCheck(env, start_response, remote_addr)
    for (url, script, l7_safe, appinfo_external) in self.handlers:
      matcher = re.match(url, path)
      if matcher and matcher.end() == len(path):




        if l7_safe or self._CheckIsTrustedIpAddress(remote_addr):


          if script:
            return self.GetUserAppAndServe(script, env, start_response)
          else:
            return self.ServeStaticFile(
                matcher, appinfo_external, env, start_response)
        else:




          redirect_url = '%s%s' % (self.l7_unsafe_redirect_url, path)
          logging.info('Returning 307 to %s for request from %s.',
                       redirect_url, remote_addr)
          start_response(
              '307 Temporary Redirect', [('location', redirect_url)])
          return ['<h1>307 Temporary Redirect</h1>\n']
    logging.error('No handler found for %s', path)
    start_response('404 Not Found', [])
    return ['<h1>404 Not Found</h1>\n']

  def ServeHealthCheck(self, env, start_response, remote_addr):
    """Serve health checks.

    It handles three cases:
    1. MVM agent is handling health check complexity:
       (1) Return ok with a 200.
    2. The request comes locally:
       (1) The IsLastSuccessful parameter will be ignored.
       (2) If there is no the previous remote check with IsLastHealthy, or that
           check has passed longer than self.check_interval_sec, it will return
           unhealthy.
       (3) Otherwise, returns status based value of self.is_last_successful.
    3. The request comes remotely:
       (1) If there is no IsLastSuccessful parameter, just return status from
           HealthHandler.
       (2) Otherwise, it sets self.is_last_successful based on the value of
           IsLastSuccessful parameter from the query string ("yes" for True,
           otherwise False), and then returns status from HealthHandler.

    Args:
      env: The WSGI environment for the application.
      start_response: The WSGI start_response for the application.
      remote_addr: The address where the request comes from.

    Returns:
      The WSGI body text iterable.
    """
    if os.environ.get('USE_MVM_AGENT') == 'true':
      start_response('200 OK', [])
      return ['ok']
    query_string = env.get('QUERY_STRING', '')
    parameters = urlparse.parse_qs(query_string)

    is_last_successful_list = parameters.get('IsLastSuccessful', None)


    if self._CheckIsLocalAddress(remote_addr):


      remote_check_valid = True
      if not self.is_last_successful_time:
        remote_check_valid = False
      else:
        time_offset_seconds = time.time() - self.is_last_successful_time
        if (time_offset_seconds >
            self.check_interval_sec * HEALTH_CHECK_INTERVAL_OFFSET_RATIO):
          remote_check_valid = False

      if self.is_last_successful and remote_check_valid:
        start_response('200 OK', [])
        return ['ok']
      else:
        start_response('500 Internal Server Error', [])
        if not self.is_last_successful:
          logging.warning('unhealthy because IsLastSuccessful is False')
        if not remote_check_valid:
          logging.warning('unhealthy because remote health check is not valid.')
        return ['unhealthy']

    else:
      if is_last_successful_list is not None:
        if is_last_successful_list[0].lower() == 'yes':
          self.is_last_successful = True
        elif is_last_successful_list[0].lower() == 'no':
          self.is_last_successful = False
        else:
          self.is_last_successful = False
          logging.warning('Wrong value for parameter IsLastSuccessful: %s',
                          is_last_successful_list)
        self.is_last_successful_time = time.time()

      return internal_app(env, start_response)

  def GetUserAppAndServe(self, script, env, start_response):
    """Dispatch a WSGI request to <script>."""
    try:
      app, mod_file = self.GetUserApp(script)
    except ImportError:
      logging.exception('Failed to import %s', script)
      start_response('500 Internal Server Error', [], sys.exc_info())
      return ['<h1>500 Internal Server Error</h1>\n']




    except ValueError:
      logging.exception('Invalid runtime.')
      start_response('500 Internal Server Error', [], sys.exc_info())
      return ['<h1>500 Internal Server Error</h1>\n']

    return self.ServeApp(app, mod_file, env, start_response)

  def ServeApp(self, app, mod_file, env, start_response):
    """(Further) wrap the provided WSGI app and dispatch a request to it."""




    for key in ENV_KEYS:
      if key in os.environ:
        del os.environ[key]
    for key in ENV_KEYS:
      assert key not in os.environ
      assert os.getenv(key) is None
    for key in self.user_env_variables:
      if key not in os.environ:
        os.environ[key] = self.user_env_variables[key]
    os.environ['AUTH_DOMAIN'] = 'gmail.com'
    os.environ['USER_IS_ADMIN'] = '0'
    for key in ENV_KEYS:
      value = env.get('HTTP_X_APPENGINE_' + key)
      if value:
        os.environ[key] = value
      elif key not in os.environ:
        os.environ[key] = ''






    user_ip = os.environ.get(WSGI_REMOTE_ADDR_ENV_KEY)
    if not user_ip:


      user_ip = env.get(X_APPENGINE_USER_IP_ENV_KEY)

    if user_ip:



      env[WSGI_REMOTE_ADDR_ENV_KEY] = user_ip


      os.environ[WSGI_REMOTE_ADDR_ENV_KEY] = user_ip



    os.environ['PATH_TRANSLATED'] = mod_file


    try:
      import appengine_config
      add_middleware = appengine_config.webapp_add_wsgi_middleware
    except (ImportError, AttributeError):
      pass
    else:
      try:
        app = add_middleware(app)
      except Exception:
        logging.exception('Failure adding WSGI middleware')


    return app(env, start_response)



  def ServeStaticFile(self, matcher, appinfo_external, unused_env,
                      start_response):
    """Serve a static file."""
    static_files = appinfo_external.static_files
    static_dir = appinfo_external.static_dir
    if static_files:
      filename = matcher.expand(static_files)
    elif static_dir:
      x = matcher.end()
      path = matcher.string
      static_dir = static_dir.lstrip('/')
      filename = static_dir + path[x:]
    filename = os.path.abspath(filename)
    pwd = os.getcwd()
    if not filename.startswith(os.path.join(pwd, '')):
      logging.warn('Requested bad filename %r', filename)
      start_response('404 Not Found', [])
      return
    try:
      fp = open(filename, 'rb')
    except IOError:
      logging.warn('Requested non-existent filename %r', filename)
      start_response('404 Not Found', [])
      return
    try:
      encoding = None
      mime_type = appinfo_external.mime_type
      if not mime_type:
        mime_type, encoding = mimetypes.guess_type(filename)
      headers = []
      if mime_type:
        headers.append(('Content-Type', mime_type))
      if encoding:
        headers.append(('Content-Encoding', encoding))

      start_response('200 OK', headers)
      while True:
        data = fp.read(8192)
        if not data:
          break
        yield data
    finally:
      fp.close()






def FixDjangoPath(libraries, sys_path):
  """Fix the entry for Django in sys.path.

  This assumes:
  - django_version contains exactly one dot (this is enforced by
    the app.yaml validation in appcfg.py).
  - sys.path contains an entry of the form '.../lib/django_0_96'
    (this is set by the vmboot.py bootstrap script).
  - Other Django versions are in sibling directories of that
    directory, if they exist in the SDK at all.

  NOTE: the 0.96 entry is removed even if we didn't find a replacement.

  Args:
    libraries: The Libraries YAML object from the AppInfoExternal.
    sys_path: The system path.

  Returns:
    A new path suitable for assigning to sys.path, including a fixed Django
    path.
  """
  if 'django' in sys.modules:
    logging.warn('Cannot fix django path, django already loaded')
    return

  django_version = 'latest'
  if libraries:
    for entry in libraries:
      if entry.name == 'django':
        django_version = entry.version
  if django_version == 'latest':
    django_version = DEFAULT_DJANGO_VERSION
  new_path = []
  django_entry = None
  for entry in sys_path:



    if entry.endswith('/lib/django-0.96'):
      new_entry = entry[:-4] + django_version
      if os.path.isdir(new_entry):
        django_entry = entry = new_entry
      else:
        entry = None
    if entry is not None:
      new_path.append(entry)
  if not django_entry:
    logging.debug('Cannot find Django version %s', django_version)
  return new_path
