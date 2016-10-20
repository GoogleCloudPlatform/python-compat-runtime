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

import datetime
import httplib
import json
import logging
from multiprocessing.pool import ThreadPool
import os
import threading
import unittest
import uuid

from google.appengine.api import appinfo
from google.appengine.ext.vmruntime import callback
from google.appengine.ext.vmruntime import utils
from mock import MagicMock
from mock import patch
from vmruntime import wsgi_config
from werkzeug import http
from werkzeug import test
from werkzeug import wrappers


class FakeDatetime(datetime.datetime):
    @staticmethod
    def now():
        return FAKE_CURRENT_TIME


def script_path(script, test_name=__name__):
    """Returns a fully qualified module path based on test_name."""
    return '{test_path}.{script}'.format(test_path=test_name, script=script)


def static_path(relative_path, test_path=os.path.dirname(__file__)):
    """Returns a fully qualified static file path based on test_path."""
    return os.path.join(test_path, relative_path)


FAKE_CURRENT_TIME = datetime.datetime(2015, 11, 30, 18)
FAKE_HTTP_HEADERS = appinfo.HttpHeadersDict()
FAKE_HTTP_HEADERS['X-Foo-Header'] = 'foo'
FAKE_HTTP_HEADERS['X-Bar-Header'] = 'bar value'

FAKE_HANDLERS = [
    appinfo.URLMap(url='/hello',
                   script=script_path('hello_world')),
    appinfo.URLMap(url='/failure',
                   script=script_path('nonexistent_function')),
    appinfo.URLMap(url='/env',
                   script=script_path('dump_os_environ')),
    appinfo.URLMap(url='/sortenv',
                   script=script_path('sort_os_environ_keys')),
    appinfo.URLMap(url='/setenv',
                   script=script_path('add_to_os_environ')),
    appinfo.URLMap(url='/wait',
                   script=script_path('wait_on_global_event')),
    appinfo.URLMap(url='/callback',
                   script=script_path('set_callback')),
    appinfo.URLMap(url='/favicon.ico',
                   static_files=static_path('test_statics/favicon.ico'),
                   upload=static_path('test_statics/favicon.ico')),
    appinfo.URLMap(url='/faketype.ico',
                   static_files=static_path('test_statics/favicon.ico'),
                   mime_type='application/fake_type',
                   upload=static_path('test_statics/favicon.ico')),
    appinfo.URLMap(url='/static_header',
                   static_files=static_path('test_statics/favicon.ico'),
                   upload=static_path('test_statics/favicon.ico'),
                   http_headers=FAKE_HTTP_HEADERS),
    appinfo.URLMap(url='/expiration',
                   static_files=static_path('test_statics/favicon.ico'),
                   upload=static_path('test_statics/favicon.ico'),
                   expiration='5d 4h'),
    appinfo.URLMap(url='/wildcard_statics/(.*)',
                   static_files=static_path(r'test_statics/\1'),
                   upload=static_path('test_statics/(.*)')),
    appinfo.URLMap(url='/static_dir',
                   static_dir=static_path('test_statics')),
]
HELLO_STRING = 'Hello World!'

FAKE_ENV_KEY = 'KEY'
FAKE_ENV_VALUE = 'VALUE'
FAKE_USER_EMAIL = 'test@example.com'
BAD_USER_EMAIL = 'bad@example.com'
FAKE_IP = '192.168.254.254'
WRONG_IP = '192.168.0.1'

FAKE_APPINFO_EXTERNAL = MagicMock(handlers=FAKE_HANDLERS,
                                  env_variables={FAKE_ENV_KEY: FAKE_ENV_VALUE,
                                                 'USER_EMAIL': BAD_USER_EMAIL},
                                  default_expiration='2d 3h')

FAKE_APPENGINE_CONFIG = MagicMock(server_software='server',
                                  partition='partition',
                                  appid='appid',
                                  module='module',
                                  instance='instance',
                                  major_version='major',
                                  minor_version='minor',
                                  default_ticket='ticket')

# Global event flags used for concurrency tests.
concurrent_request_is_started = threading.Event()
concurrent_request_should_proceed = threading.Event()

# Global flags used for callback tests.
callback_called = False

# These tests will deliberately cause ERROR level logs, so let's disable them.
logging.basicConfig(level=logging.CRITICAL)


@wrappers.Request.application
def hello_world(request):  # pylint: disable=unused-argument
    return wrappers.Response(HELLO_STRING)


@wrappers.Request.application
def dump_os_environ(request):  # pylint: disable=unused-argument
    return wrappers.Response(json.dumps(dict(os.environ)))


@wrappers.Request.application
def add_to_os_environ(request):  # pylint: disable=unused-argument
    os.environ['ENVIRONMENT_MODIFIED'] = 'TRUE'
    return wrappers.Response(json.dumps(dict(os.environ)))


@wrappers.Request.application
def wait_on_global_event(request):  # pylint: disable=unused-argument
    concurrent_request_is_started.set()
    concurrent_request_should_proceed.wait()
    return wrappers.Response(json.dumps(dict(os.environ)))


@wrappers.Request.application
def sort_os_environ_keys(request):  # pylint: disable=unused-argument
    # See test_env_sort method for explanation.
    return wrappers.Response(''.join('%s=%s\n' % (
        k, v) for k, v in sorted(os.environ.iteritems())))


@wrappers.Request.application
def set_callback(request):
    def my_callback(unused_req_id=None):
        global callback_called
        callback_called = True

    utils.SetRequestId(str(uuid.uuid4()))

    callback.SetRequestEndCallback(my_callback)
    return wrappers.Response("pass!")

class EnableAppEngineApisTestCase(unittest.TestCase):
    def test_enable_app_engine_apis_warning(self):
        from google.appengine.ext.vmruntime import vmconfig
        with patch.object(wsgi_config, 'get_module_config_filename') as m:
            m.side_effect = KeyError('MODULE_YAML_PATH')
            with self.assertRaises(RuntimeError) as a:
                from vmruntime import wsgi
            self.assertIn('enable_app_engine_apis: true', a.exception.args[0])


class MetaAppTestCase(unittest.TestCase):
    def setUp(self):
        # pylint: disable=g-import-not-at-top
        # Pre-import modules to patch them in advance.
        from google.appengine.ext.vmruntime import vmconfig

        # Instantiate an app with a simple fake configuration.
        with patch.object(wsgi_config, 'get_module_config_filename'):
            with patch.object(wsgi_config,
                              'get_module_config',
                              return_value=FAKE_APPINFO_EXTERNAL):
                with patch.object(vmconfig,
                                  'BuildVmAppengineEnvConfig',
                                  return_value=FAKE_APPENGINE_CONFIG):
                    from vmruntime import wsgi
                    self.app = wsgi.meta_app
        self.client = test.Client(self.app, wrappers.Response)
        # Separate client for concurrent tests.
        self.spare_client = test.Client(self.app, wrappers.Response)

        # Clear the global event flags (only used in concurrency tests).
        concurrent_request_is_started.clear()
        concurrent_request_should_proceed.clear()


    def test_hello(self):
        response = self.client.get('/hello')
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.data, HELLO_STRING)

    def test_failure(self):
        response = self.client.get('/failure')
        self.assertEqual(response.status_code, httplib.INTERNAL_SERVER_ERROR)

    def test_notfound(self):
        response = self.client.get('/notfound')
        self.assertEqual(response.status_code, httplib.NOT_FOUND)

    def test_health(self):
        response = self.client.get('/_ah/health')
        self.assertEqual(response.status_code, httplib.OK)

    # Test PATH is present in env. If this breaks, each request is properly
    # wiping the environment but not properly reconstituting the frozen initial
    # state.
    def test_basic_env(self):
        response = self.client.get('/env')
        # Assumes PATH will be present in the env in all cases, including
        # tests!
        self.assertIn('PATH', json.loads(response.data))

    def test_static_file(self):
        response = self.client.get('/favicon.ico')
        self.assertEqual(response.status_code, httplib.OK)
        with open(static_path('test_statics/favicon.ico')) as f:
            self.assertEqual(response.data, f.read())

    def test_static_file_mime_type(self):
        response = self.client.get('/faketype.ico')
        self.assertEqual(response.status_code, httplib.OK)
        with open(static_path('test_statics/favicon.ico')) as f:
            self.assertEqual(response.data, f.read())
        self.assertEqual(response.mimetype, 'application/fake_type')

    def test_static_file_header(self):
        response = self.client.get('/static_header')
        self.assertEqual(response.status_code, httplib.OK)
        with open(static_path('test_statics/favicon.ico')) as f:
            self.assertEqual(response.data, f.read())
        self.assertTrue('X-Foo-Header' in response.headers)
        self.assertEqual(response.headers['X-Foo-Header'], 'foo')
        self.assertTrue('X-Bar-Header' in response.headers)
        self.assertEqual(response.headers['X-Bar-Header'], 'bar value')

    @patch('datetime.datetime', FakeDatetime)
    def test_static_file_expires(self):
        response = self.client.get('/expiration')
        self.assertEqual(response.status_code, httplib.OK)
        with open(static_path('test_statics/favicon.ico')) as f:
            self.assertEqual(response.data, f.read())
        current_time = FAKE_CURRENT_TIME
        extra_time = datetime.timedelta(
            seconds=appinfo.ParseExpiration('5d 4h'))
        expired_time = current_time + extra_time
        self.assertEqual(response.headers['Expires'],
                         http.http_date(expired_time))

    @patch('datetime.datetime', FakeDatetime)
    def test_static_file_default_expires(self):
        response = self.client.get('/favicon.ico')
        self.assertEqual(response.status_code, httplib.OK)
        with open(static_path('test_statics/favicon.ico')) as f:
            self.assertEqual(response.data, f.read())
        current_time = FAKE_CURRENT_TIME
        extra_time = datetime.timedelta(
            seconds=appinfo.ParseExpiration('2d 3h'))
        expired_time = current_time + extra_time
        self.assertEqual(response.headers['Expires'],
                         http.http_date(expired_time))

    def test_static_file_wildcard(self):
        response = self.client.get('/wildcard_statics/favicon.ico')
        self.assertEqual(response.status_code, httplib.OK)
        with open(static_path('test_statics/favicon.ico')) as f:
            self.assertEqual(response.data, f.read())

    def test_static_file_wildcard_404(self):
        response = self.client.get('/wildcard_statics/no_file')
        self.assertEqual(response.status_code, httplib.NOT_FOUND)

    def test_static_file_wildcard_directory_traversal(self):
        # Try to fetch some files outside of the "upload" regex using path
        # traversal
        response = self.client.get('/wildcard_statics/../../setup.py')
        self.assertEqual(response.status_code, httplib.NOT_FOUND)
        response = self.client.get('/wildcard_statics/../__init__.py')
        self.assertEqual(response.status_code, httplib.NOT_FOUND)

    def test_static_dir(self):
        response = self.client.get('/static_dir/favicon.ico')
        self.assertEqual(response.status_code, httplib.OK)
        with open(static_path('test_statics/favicon.ico')) as f:
            self.assertEqual(response.data, f.read())

    def test_wsgi_vars_in_env(self):
        response = self.client.get('/env')
        env = json.loads(response.data)
        self.assertEqual(env['REQUEST_METHOD'], 'GET')
        self.assertEqual(env['QUERY_STRING'], '')

    def test_header_data_in_env(self):
        response = self.client.get(
            '/env',
            headers={'X_APPENGINE_USER_EMAIL': FAKE_USER_EMAIL})
        env = json.loads(response.data)
        self.assertEqual(env['AUTH_DOMAIN'], 'gmail.com')
        self.assertEqual(env['USER_IS_ADMIN'], '0')
        self.assertEqual(env['REQUEST_LOG_ID'], '')
        self.assertEqual(env['USER_EMAIL'], FAKE_USER_EMAIL)

    def test_appengine_config_data_in_env(self):
        response = self.client.get('/env')
        env = json.loads(response.data)
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
        # USER_EMAIL is a reserved key and doesn't allow user env vars to
        # override.
        self.assertNotEqual(env['USER_EMAIL'], BAD_USER_EMAIL)

    def test_service_bridge_hidden_in_env(self):
        response = self.client.get('/env', headers={'X_APPENGINE_HTTPS': 'on'})
        env = json.loads(response.data)
        self.assertEqual(env['SERVER_PORT'], '443')

    def test_remote_addr_in_env(self):
        response = self.client.get('/env',
                                   headers={'X_APPENGINE_USER_IP': FAKE_IP})
        env = json.loads(response.data)
        self.assertEqual(env['REMOTE_ADDR'], FAKE_IP)

        response = self.client.get('/env',
                                   headers={'X_APPENGINE_REMOTE_ADDR': FAKE_IP,
                                            'X_APPENGINE_USER_IP': WRONG_IP})
        env = json.loads(response.data)
        self.assertEqual(env['REMOTE_ADDR'], FAKE_IP)

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
        future = pool.apply_async(self.client.get, ('/wait', ))

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
        self.assertEqual(response.status_code, httplib.OK)
        # If the handler didn't crash, the regression test passed. No need to
        # validate contents extensively.
        self.assertIn('REQUEST_METHOD', response.data)
        self.assertIn('GET', response.data)

    # Tests the callback middleware.
    def test_callback(self):
      self.assertFalse(callback_called)
      response = self.client.get('/callback')
      self.assertEqual(response.status_code, httplib.OK)
      self.assertTrue(callback_called)
