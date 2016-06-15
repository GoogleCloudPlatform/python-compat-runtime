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

import json
import logging
import os
import unittest

import mock
from vmruntime import cloud_logging


class CloudLoggingTestCase(unittest.TestCase):

    EXPECTED_TRACE_ID = None
    EXPECTED_OVERRIDDEN_TRACE_ID = '1234abcd1234abcd1234abcd1234abcd'
    EXPECTED_MESSAGE = 'test message'
    TEST_TIME = 1437589520.830589056
    EXPECTED_SECONDS = 1437589520
    EXPECTED_NANOS = 830589056

    @mock.patch.object(cloud_logging.CloudLoggingHandler, '_open')
    def setUp(self, mock_open):
        self.handler = cloud_logging.CloudLoggingHandler()
        with mock.patch('time.time', return_value=self.TEST_TIME):
            self.record = logging.makeLogRecord({'msg': self.EXPECTED_MESSAGE,
                                                 'levelname': 'INFO'})
            self.record_with_extra = logging.makeLogRecord(
                {'msg': self.EXPECTED_MESSAGE,
                 'levelname': 'INFO',
                 'trace_id': self.EXPECTED_OVERRIDDEN_TRACE_ID, })

    def test_file_name_is_correct(self):
        self.assertTrue(self.handler.baseFilename.startswith(
            '/var/log/app_engine/app.'))
        self.assertTrue(self.handler.baseFilename.endswith('.json'))

    def test_format(self):
        msg = self.handler.format(self.record)
        payload = json.loads(msg)
        if self.EXPECTED_TRACE_ID:
            self.assertEquals(payload['traceId'], self.EXPECTED_TRACE_ID)
        else:
            self.assertNotIn('traceId', payload)

    def test_format_with_trace_id_as_extra(self):
        msg = self.handler.format(self.record_with_extra)
        payload = json.loads(msg)
        self.assertEquals(payload['traceId'],
                          self.EXPECTED_OVERRIDDEN_TRACE_ID)

    def test_format_timestamp(self):
        msg = self.handler.format(self.record)
        payload = json.loads(msg)
        self.assertEquals(payload['timestamp']['seconds'],
                          self.EXPECTED_SECONDS)
        self.assertEquals(payload['timestamp']['nanos'], self.EXPECTED_NANOS)


class CloudLoggingTestCaseWithTraceIdEnv(CloudLoggingTestCase):

    EXPECTED_TRACE_ID = '01010101020202020303030304040404'

    def setUp(self):
        super(CloudLoggingTestCaseWithTraceIdEnv, self).setUp()
        os.environ['HTTP_X_CLOUD_TRACE_CONTEXT'] = '{}/12345;o=1'.format(
            self.EXPECTED_TRACE_ID)

    def tearDown(self):
        os.unsetenv('HTTP_X_CLOUD_TRACE_CONTEXT')


class CloudLoggingTestCaseWithTraceIdEnvNoOptions(CloudLoggingTestCase):

    EXPECTED_TRACE_ID = '0101010102020202ababababcdcdcdcd'

    def setUp(self):
        super(CloudLoggingTestCaseWithTraceIdEnvNoOptions, self).setUp()
        os.environ['HTTP_X_CLOUD_TRACE_CONTEXT'] = self.EXPECTED_TRACE_ID

    def tearDown(self):
        os.unsetenv('HTTP_X_CLOUD_TRACE_CONTEXT')
