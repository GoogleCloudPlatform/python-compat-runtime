# Copyright 2016 Google Inc. All Rights Reserved.
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

import logging
import os

from google.appengine.api.logservice import logservice
import pytest


@pytest.fixture
def request_id():
    return os.environ.get('REQUEST_LOG_ID')


@pytest.mark.xfail
def do_not_run_test_logservice_fetch(request_id):
    """This test fails at logservice.fetch"""
    logging.info('TESTING')
    found_log = False
    for req_log in logservice.fetch(request_ids=[request_id],
                                    include_app_logs=True):
        for app_log in req_log.app_logs:
            if app_log.message == 'TESTING':
                found_log = True

    assert found_log
