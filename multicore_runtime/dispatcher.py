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
"""A WSGI app that, once configured, dispatches requests to user apps."""

import logging
import re

from werkzeug.wrappers import Request
from werkzeug.wrappers import Response


def dispatcher(handlers):
  """Accepts handlers and returns a WSGI app that dispatches requests to them.

  Args:
    handlers: a list of handlers as produced by
      wsgi_utils.load_user_scripts_into_handlers: a list of tuples of
      (url, script, app).

  Returns:
    A WSGI app that dispatches to the user apps specified in the input.
  """

  def dispatch(wsgi_env, start_response):
    """Handle one request."""
    request = Request(wsgi_env)
    for url, script, app in handlers:  # pylint: disable=unused-variable
      matcher = re.match(url, request.path)
      if matcher and matcher.end() == len(request.path):
        if app is not None:
          # Send a response via the app specified in the handler.
          return app(wsgi_env, start_response)
        else:
          # The import must have failed. This will have been logged at import
          # time. Send a 500 error response.
          response = Response('<h1>500 Internal Server Error</h1>\n',
                              status=500)
          return response(wsgi_env, start_response)
    logging.error('No handler found for %s', request.path)
    start_response('404 Not Found', [])
    return ['<h1>404 Not Found</h1>\n']

  return dispatch
