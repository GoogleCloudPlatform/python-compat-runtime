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

import logging
import sys

from google.appengine import api
from google.appengine.api import app_logging




from google.appengine.api.logservice import logservice
from google.appengine.ext.vmruntime import background_thread
from google.appengine.runtime import request_environment
from google.appengine.runtime import runtime

LOG_FORMAT = '%(asctime)s %(threadName)s %(levelname)s %(message)s'
APP_LOG_FILE = '/var/log/app_engine/app.log'


def InitializeFileLogging():
  """Helper called from CreateAndRunService() to set up syslog logging."""




  logging.basicConfig()


  logger = logging.getLogger()
  logger.handlers = []


  file_handler = logging.FileHandler(APP_LOG_FILE)
  file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
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

  sys.modules[api.__name__ + '.background_thread'] = background_thread
  api.background_thread = background_thread
