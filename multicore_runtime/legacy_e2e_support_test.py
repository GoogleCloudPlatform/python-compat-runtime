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
import tempfile
import unittest

from werkzeug.test import Client
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

import legacy_e2e_support


class LegacyAppConfigTestCase(unittest.TestCase):

  def test_legacy_app_for_script(self):
    app = legacy_e2e_support.legacy_app_for_script(
        'legacy_e2e_support_test_app.py')
    client = Client(app, Response)
    response = client.get('/')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data, 'Hello World!')
