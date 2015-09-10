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
import httplib
import unittest

from mock import patch
from werkzeug import test
from werkzeug import wrappers

from . import wsgi_config
from . import wsgi_test

@wrappers.Request.application
def salutation_world(request):
  salutation = request.args.get('salutation', 'Hello')
  return wrappers.Response('%s World!' % salutation)


def goodbye_world_middleware(app):
  def goodbye_wrapper(wsgi_env, start_response):
    wsgi_env['QUERY_STRING'] = 'salutation=Goodbye'
    return app(wsgi_env, start_response)
  return goodbye_wrapper


class AppConfigTestCase(unittest.TestCase):

  def test_app_for_script(self):
    with patch.object(wsgi_config, 'get_add_middleware_from_appengine_config',
               return_value=None):
      app = wsgi_config.app_for_script(
          wsgi_test.script_path('salutation_world', test_name=__name__))
    client = test.Client(app, wrappers.Response)
    response = client.get('/?salutation=Hello')
    self.assertEqual(response.status_code, httplib.OK)
    self.assertEqual(response.data, 'Hello World!')

  def test_app_for_script_with_middleware(self):
    with patch.object(wsgi_config, 'get_add_middleware_from_appengine_config',
               return_value=goodbye_world_middleware):
      app = wsgi_config.app_for_script(
          wsgi_test.script_path('salutation_world', test_name=__name__))
    client = test.Client(app, wrappers.Response)
    response = client.get('/?salutation=Hello')
    self.assertEqual(response.status_code, httplib.OK)
    self.assertEqual(response.data, 'Goodbye World!')
