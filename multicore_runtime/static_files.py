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
"""Static file serving functionality invoked by wsgi_config.py."""

import logging
import mimetypes
import os
import re

from werkzeug.wrappers import Request
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file


def static_app_for_regex_and_files(regex, files, mime_type=None):
  """Returns a WSGI app that serves static files.

  Args:
    regex: A url-matching regex as specified in appinfo.URLMap.
    files: A static_files definition as specified in appinfo.URLMap.
        May include a regex backref. See the appinfo.URLMap docstring
        for more information.
    mime_type: A mime type to apply to all files. If absent,
        mimetypes.guess_type() is used.

  Returns:
    A static file-serving WSGI app closed over the inputs.
  """
  @Request.application  # Transforms wsgi_env, start_response args into request
  def serve_static_files(request):
    """Serve a static file."""
    # First, match the path against the regex...
    matcher = re.match(regex, request.path)
    # ... and use the files regex backref to choose a filename.
    filename = matcher.expand(files)

    # Rudimentary protection against path traversal outside of the app. This
    # code should never be hit in production, as Google's frontend servers
    # (GFE) rewrite traversal attempts and respond with a 302 immediately.
    filename = os.path.abspath(filename)
    if not filename.startswith(os.path.join(os.getcwd(), '')):
      logging.warn('Path traversal protection triggered for %s, '
                   'returning 404', filename)
      return Response(status=404)

    try:
      fp = open(filename, 'rb')
      # fp is not closed in this function as it is handed to the WSGI server
      # directly.
    except IOError:
      logging.warn('Requested non-existent filename %s', filename)
      return Response(status=404)

    wrapped_file = wrap_file(request.environ, fp)
    return Response(wrapped_file, direct_passthrough=True,
                    mimetype=mime_type or mimetypes.guess_type(filename)[0])
  return serve_static_files
