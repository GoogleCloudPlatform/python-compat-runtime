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
# pylint: disable=g-import-not-at-top

import json
import logging
from multiprocessing.pool import ThreadPool
import os
import threading
import unittest

from mock import MagicMock
from mock import patch
from werkzeug.test import Client
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

from google.appengine.api import appinfo

FAKE_HANDLERS = [
    appinfo.URLMap(url='/hello', script='wsgi_test.hello_world'),
    appinfo.URLMap(url='/failure', script='wsgi_test.nonexistent_function'),
    appinfo.URLMap(url='/env', script='wsgi_test.dump_os_environ'),
    appinfo.URLMap(url='/sortenv', script='wsgi_test.sort_os_environ_keys'),
    appinfo.URLMap(url='/setenv', script='wsgi_test.add_to_os_environ'),
    appinfo.URLMap(url='/wait', script='wsgi_test.wait_on_global_event'),
    appinfo.URLMap(url='/login', script='wsgi_test.hello_world',
                   login=appinfo.LOGIN_REQUIRED),
    appinfo.URLMap(url='/admin', script='wsgi_test.hello_world',
                   login=appinfo.LOGIN_ADMIN),
    appinfo.URLMap(url='/favicon.ico',
                   static_files='test_statics/favicon.ico',
                   upload='test_statics/favicon.ico'),
    appinfo.URLMap(url='/faketype.ico', static_files='test_statics/favicon.ico',
                   mime_type='application/fake_type',
                   upload='test_statics/favicon.ico'),
    appinfo.URLMap(url='/wildcard_statics/(.*)',
                   static_files=r'test_statics/\1',
                   upload='test_statics/(.*)'),
    appinfo.URLMap(url='/static_dir',
                   static_dir='test_statics'),
    ]
HELLO_STRING = 'Hello World!'

FAKE_ENV_KEY = 'KEY'
FAKE_ENV_VALUE = 'VALUE'
FAKE_USER_EMAIL = 'test@example.com'
BAD_USER_EMAIL = 'bad@example.com'

FAKE_APPINFO_EXTERNAL = MagicMock(handlers=FAKE_HANDLERS,
                                  env_variables={FAKE_ENV_KEY: FAKE_ENV_VALUE,
                                                 'USER_EMAIL': BAD_USER_EMAIL})

FAKE_APPENGINE_CONFIG = MagicMock(
    server_software='server', partition='partition', appid='appid',
    module='module', instance='instance', major_version='major',
    minor_version='minor', default_ticket='ticket')


# Global event flags used for concurrency tests.
concurrent_request_is_started = threading.Event()
concurrent_request_should_proceed = threading.Event()

# These tests will deliberately cause ERROR level logs, so let's disable them.
logging.basicConfig(level=logging.CRITICAL)


@Request.application
def hello_world(request):  # pylint: disable=unused-argument
  return Response(HELLO_STRING)


@Request.application
def dump_os_environ(request):  # pylint: disable=unused-argument
  return Response(json.dumps(dict(os.environ)))


@Request.application
def add_to_os_environ(request):  # pylint: disable=unused-argument
  os.environ['ENVIRONMENT_MODIFIED'] = 'TRUE'
  return Response(json.dumps(dict(os.environ)))


@Request.application
def wait_on_global_event(request):  # pylint: disable=unused-argument
  concurrent_request_is_started.set()
  concurrent_request_should_proceed.wait()
  return Response(json.dumps(dict(os.environ)))


@Request.application
def sort_os_environ_keys(request):  # pylint: disable=unused-argument
  # See test_env_sort method for explanation.
  resp = ""
  for name in sorted(os.environ):
    resp += '%s=%s\n' % (name, os.environ[name])
  return Response(resp)


class MetaAppTestCase(unittest.TestCase):

  def setUp(self):
    # Pre-import modules to patch them in advance.
    from google.appengine.ext.vmruntime import vmconfig  # pylint: disable=unused-variable

    # Instantiate an app with a simple fake configuration.
    with patch('wsgi_config.get_module_config_filename'):
      with patch('wsgi_config.get_module_config',
                 return_value=FAKE_APPINFO_EXTERNAL):
        with patch('google.appengine.ext.vmruntime.vmconfig.BuildVmAppengineEnvConfig',  # pylint: disable=line-too-long
                   return_value=FAKE_APPENGINE_CONFIG):
          import wsgi
          self.app = wsgi.meta_app
    self.client = Client(self.app, Response)
    # Separate client for concurrent tests.
    self.spare_client = Client(self.app, Response)

    # Clear the global event flags (only used in concurrency tests).
    concurrent_request_is_started.clear()
    concurrent_request_should_proceed.clear()

  def test_hello(self):
    response = self.client.get('/hello')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data, HELLO_STRING)

  def test_failure(self):
    response = self.client.get('/failure')
    self.assertEqual(response.status_code, 500)

  def test_notfound(self):
    response = self.client.get('/notfound')
    self.assertEqual(response.status_code, 404)

  def test_health(self):
    response = self.client.get('/_ah/health')
    self.assertEqual(response.status_code, 200)

  # Test PATH is present in env. If this breaks, each request is properly
  # wiping the environment but not properly reconstituting the frozen initial
  # state.
  def test_basic_env(self):
    response = self.client.get('/env')
    # Assumes PATH will be present in the env in all cases, including tests!
    self.assertIn('PATH', json.loads(response.data))

  def test_login_required(self):
    # Login routes are temporarily disabled.
    response = self.client.get('/login')
    self.assertEqual(response.status_code, 404)

  def test_login_admin(self):
    # Login routes are temporarily disabled.
    response = self.client.get('/admin')
    self.assertEqual(response.status_code, 404)

  def test_static_file(self):
    response = self.client.get('/favicon.ico')
    self.assertEqual(response.status_code, 200)
    with open('test_statics/favicon.ico') as f:
      self.assertEqual(response.data, f.read())

  def test_static_file_mime_type(self):
    response = self.client.get('/faketype.ico')
    self.assertEqual(response.status_code, 200)
    with open('test_statics/favicon.ico') as f:
      self.assertEqual(response.data, f.read())
    self.assertEqual(response.mimetype, 'application/fake_type')

  def test_static_file_wildcard(self):
    response = self.client.get('/wildcard_statics/favicon.ico')
    self.assertEqual(response.status_code, 200)
    with open('test_statics/favicon.ico') as f:
      self.assertEqual(response.data, f.read())

  def test_static_file_wildcard_404(self):
    response = self.client.get('/wildcard_statics/no_file')
    self.assertEqual(response.status_code, 404)

  def test_static_file_wildcard_directory_traversal(self):
    # Try to fetch some files outside of the "upload" regex using path traversal
    response = self.client.get('/wildcard_statics/../../setup.py')
    self.assertEqual(response.status_code, 404)
    response = self.client.get('/wildcard_statics/../__init__.py')
    self.assertEqual(response.status_code, 404)

  def test_static_dir(self):
    response = self.client.get('/static_dir/favicon.ico')
    self.assertEqual(response.status_code, 200)
    with open('test_statics/favicon.ico') as f:
      self.assertEqual(response.data, f.read())

  def test_wsgi_vars_in_env(self):
    response = self.client.get('/env')
    env = json.loads(response.data)
    self.assertEqual(env['REQUEST_METHOD'], 'GET')
    self.assertEqual(env['QUERY_STRING'], '')

  def test_header_data_in_env(self):
    response = self.client.get(
        '/env', headers={'X_APPENGINE_USER_EMAIL': FAKE_USER_EMAIL})
    env = json.loads(response.data)
    self.assertEqual(env['AUTH_DOMAIN'], 'gmail.com')
    self.assertEqual(env['USER_IS_ADMIN'], '0')
    self.assertEqual(env['REQUEST_LOG_ID'], '')
    self.assertEqual(env['USER_EMAIL'], FAKE_USER_EMAIL)

  def test_appengine_config_data_in_env(self):
    response = self.client.get('/env')
    env = json.loads(response.data)
    self.assertEqual(env['SERVER_SOFTWARE'], 'server')
    self.assertEqual(env['APPENGINE_RUNTIME'], 'python27')
    self.assertEqual(env['APPLICATION_ID'], 'partition~appid')
    self.assertEqual(env['INSTANCE_ID'], 'instance')
    self.assertEqual(env['BACKEND_ID'], 'major')
    self.assertEqual(env['CURRENT_MODULE_ID'], 'module')
    self.assertEqual(env['CURRENT_VERSION_ID'], 'major.minor')
    self.assertEqual(env['DEFAULT_TICKET'], 'ticket')

  def test_user_env_vars_in_env(self):
    response = self.client.get('/env')
    env = json.loads(response.data)
    self.assertEqual(env[FAKE_ENV_KEY], FAKE_ENV_VALUE)
    # USER_EMAIL is a reserved key and doesn't allow user env vars to override.
    self.assertNotEqual(env['USER_EMAIL'], BAD_USER_EMAIL)

  def test_service_bridge_hidden_in_env(self):
    response = self.client.get('/env', headers={'X_APPENGINE_HTTPS': 'on'})
    env = json.loads(response.data)
    self.assertEqual(env['SERVER_PORT'], '443')

  # Test that one request can't modify the environment in a way that affects
  # a subsequent request. This validates os.environ is cleared per request.
  def test_requests_have_independent_env(self):
    response = self.client.get('/setenv')
    self.assertIn('ENVIRONMENT_MODIFIED', json.loads(response.data))

    response = self.client.get('/env')
    self.assertNotIn('ENVIRONMENT_MODIFIED', json.loads(response.data))

  # Test that one request can't modify the environment in a way that affects
  # concurrent requests. This validates that os.environ is thread-local.
  def test_concurrent_requests_have_independent_env(self):
    # First, start a separate thread that starts a request but then hangs.
    pool = ThreadPool(processes=1)
    future = pool.apply_async(self.client.get, ('/wait',))

    # Block until the second thread is in the request phase to be sure it's
    # finished initializing its environment in middleware.
    success = concurrent_request_is_started.wait(5)
    self.assertTrue(success)  # If this fails, the event never fired.

    # In the main thread, fire a request that mutates the environment.
    response = self.spare_client.get('/setenv')
    self.assertIn('ENVIRONMENT_MODIFIED', json.loads(response.data))

    # Trip the flag so the thread can finish.
    concurrent_request_should_proceed.set()

    # Wait for the thread to finish and examine the results.
    response = future.get(5)  # This will raise an exception on timeout.
    self.assertNotIn('ENVIRONMENT_MODIFIED', json.loads(response.data))

  # Regression test for an issue where a threadlocal dict subclass could not
  # be cast to a list or sorted.
  def test_env_sort(self):
    response = self.client.get('/sortenv')
    self.assertEqual(response.status_code, 200)
    # If the handler didn't crash, the regression test passed. No need to
    # validate contents extensively.
    self.assertIn('REQUEST_METHOD', response.data)
    self.assertIn('GET', response.data)
