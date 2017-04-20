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

import unittest
from mock import MagicMock
from mock import patch

from werkzeug.test import Client
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

from google.appengine.api import appinfo

FAKE_HANDLERS = [
    appinfo.URLMap(url='/hello', script='wsgi_test.hello_world'),
    appinfo.URLMap(url='/failure', script='wsgi_test.nonexistent_function')]
HELLO_STRING = 'Hello World!'


@Request.application
def hello_world(request):  # pylint: disable=unused-argument
  return Response(HELLO_STRING)


class MetaAppTestCase(unittest.TestCase):

  def setUp(self):
    # Pre-import modules to patch them in advance.
    from google.appengine.ext.vmruntime import vmconfig  # pylint: disable=unused-variable

    # Instantiate an app with a simple fake configuration.
    with patch('wsgi_utils.get_module_config_filename'):
      with patch('wsgi_utils.get_module_config',
                 return_value=MagicMock(handlers=FAKE_HANDLERS)):
        with patch('google.appengine.ext.vmruntime.vmconfig.BuildVmAppengineEnvConfig'):  # pylint: disable=line-too-long
          import wsgi
          self.app = wsgi.meta_app
    self.client = Client(self.app, Response)

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
