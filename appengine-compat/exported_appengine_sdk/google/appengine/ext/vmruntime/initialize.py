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
"""Functions that prepare GAE user code for running in a GCE VM."""

import json
import logging
import logging.handlers
import math
import sys
import traceback

from google.appengine import api
from google.appengine.api import app_logging




from google.appengine.api.logservice import logservice
from google.appengine.ext.vmruntime import background_thread
from google.appengine.ext.vmruntime import utils
from google.appengine.runtime import request_environment
from google.appengine.runtime import runtime


APP_LOG_FILE = '/var/log/app_engine/app.log.json'


MAX_LOG_BYTES = 128 * 1024 * 1024


LOG_BACKUP_COUNT = 3


class JsonFormatter(logging.Formatter):
  """Class for logging to the cloud logging api with json metadata."""

  def format(self, record):
    """Format the record as json the cloud logging agent understands.

    Args:
      record: A logging.LogRecord to format.

    Returns:
      A json string to log.
    """
    float_frac_sec, float_sec = math.modf(record.created)

    data = {'thread': record.thread,
            'timestamp': {
                'seconds': int(float_sec),
                'nanos': int(float_frac_sec * 1000000000)}}

    if record.exc_info:

      data['message'] = '%s\n%s' % (record.getMessage(),
                                    traceback.format_exc(
                                        record.exc_info))
      data['severity'] = 'CRITICAL'
    else:
      data['message'] = record.getMessage()
      data['severity'] = record.levelname
    return json.dumps(data)


def InitializeFileLogging():
  """Helper called from CreateAndRunService() to set up syslog logging."""




  logging.basicConfig()


  logger = logging.getLogger()
  logger.handlers = []


  file_handler = logging.handlers.RotatingFileHandler(
      APP_LOG_FILE, maxBytes=MAX_LOG_BYTES, backupCount=LOG_BACKUP_COUNT)
  file_handler.setFormatter(JsonFormatter())
  logger.addHandler(file_handler)

  logger.setLevel(logging.DEBUG)


def InitializeApiLogging():
  """Helper called from CreateAndRunService() to set up api logging."""








  logservice.logs_buffer = lambda: request_environment.current_request.errors

  logger = logging.getLogger()
  app_log_handler = app_logging.AppLogsHandler()
  logger.addHandler(app_log_handler)








def InitializeThreadingApis():
  """Helper to monkey-patch various threading APIs."""



  runtime.PatchStartNewThread()
  utils.PatchStartNewThread()

  sys.modules[api.__name__ + '.background_thread'] = background_thread
  api.background_thread = background_thread
