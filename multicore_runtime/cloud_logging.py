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
"""Provide a handler to log to Cloud Logging in JSON."""

import json
import logging
import math
import os

LOG_PATH_TEMPLATE = '/var/log/app_engine/app.{}.json'


class CloudLoggingHandler(logging.FileHandler):
  """A handler that emits logs to Cloud Logging.

  Writes to the Cloud Logging directory, wrapped in JSON and with appropriate
  metadata. The process of converting the user's formatted logs into a JSON
  payload for Cloud Logging consumption is implemented as part of the handler
  itself, and not as a formatting step, so as not to interfere with user-defined
  logging formats.

  The handler will look for HTTP header information in the environment (which
  will be present in the GAE 1.0-compatible runtime) and, if it exists, will
  parse the X-Cloud-Trace-Context header to add a Trace ID to each log record.

  Logging calls can also alternatively 'trace_id' in as a field in the 'extra'
  dict, which will be used preferentially to fill out the Trace ID metadata.
  """

  def __init__(self):
    # Large log entries will get mangled if multiple workers write to the same
    # file simultaneously, so we'll use the worker's PID to pick a log filename.
    filename = LOG_PATH_TEMPLATE.format(os.getpid())
    super(CloudLoggingHandler, self).__init__(filename)

  def format(self, record):
    """Format the specified record default behavior, plus JSON and metadata."""
    # First, let's just get the log string as it would normally be formatted.
    message = super(CloudLoggingHandler, self).format(record)

    # Now assemble a dictionary with the log string as the message.
    payload = {
        'message': message,
        'timestamp': {'seconds': int(record.created),
                      'nanos': int(math.modf(record.created)[0] * 1000000000)},
        'thread': record.thread,
        'severity': record.levelname,}

    # Now make a best effort to add the trace id.
    # First, try to get the trace id from the 'extras' of the record.
    trace_id = getattr(record, 'trace_id', None)

    # If that didn't work, check if HTTP headers are present in the
    # environment (GAE 1.0-style), and use them to parse out the Trace ID.
    if not trace_id:
      trace_id = os.getenv('X-Cloud-Trace-Context', '')[:16]

    # Now add a traceID key to the payload, if one was found.
    if trace_id:
      payload['traceId'] = trace_id

    return json.dumps(payload)
