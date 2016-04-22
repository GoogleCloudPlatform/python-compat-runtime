"""E2E test for logging API.

Currently DOES NOT work.
"""
import json
import logging
import os
import pytest

from google.appengine.api.logservice import logservice


@pytest.fixture
def request_id():
  return os.environ.get('REQUEST_LOG_ID')

def test_log(request_id):
  logging.info('TESTING')


# This test must happen after test_log.
def do_not_run_test_logservice_fetch(request_id):
  """This test fails at logservice.fetch"""
  found_log = False
  for req_log in logservice.fetch(
      request_ids=[request_id],
      include_app_logs=True):
    for app_log in req_log.app_logs:
      if app_log.message == 'TESTING':
        found_log = True

  assert found_log

