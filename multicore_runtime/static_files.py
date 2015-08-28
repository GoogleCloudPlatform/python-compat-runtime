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

import httplib
import logging
import mimetypes
import os
import re

from werkzeug import wrappers
from werkzeug import wsgi


def static_app_for_regex_and_files(url_re, files_mapping, upload_re,
                                   mime_type=None):
  """Returns a WSGI app that serves static files.

  Args:
    url_re: A url-matching regex as specified in appinfo.URLMap.
    files_mapping: A static_files definition as specified in appinfo.URLMap.
      May include a regex backref. See the appinfo.URLMap docstring
      for more information.
    upload_re: A filename-matching regex as specified in appinfo.URLMap.
      Only files that match this regex will be served regardless of other
      arguments.
    mime_type: A mime type to apply to all files. If absent,
      mimetypes.guess_type() is used.

  Returns:
    A static file-serving WSGI app closed over the inputs.
  """
  @wrappers.Request.application  # Transforms wsgi_env, start_response args into request
  def serve_static_files(request):
    """Serve a static file."""
    # First, match the path against the regex.
    matcher = re.match(url_re, request.path)
    if not matcher:  # Just for safety - the dispatcher should have matched this
      logging.error('Static file handler found no match for %s',
                    request.path)
      return wrappers.Response(status=httplib.NOT_FOUND)

    # Use the match and the files regex backref to choose a filename.
    filename = matcher.expand(files_mapping)

    # Check to see if the normalized path matched is in the upload regex.
    # This provides path traversal protection, although apps running on Google
    # servers are protected by the Google frontend (GFE)'s own path traversal
    # protection as well.
    if not re.match(upload_re, os.path.normpath(filename)):
      logging.warn('Requested filename %s not in `upload`', filename)
      return wrappers.Response(status=httplib.NOT_FOUND)

    try:
      fp = open(filename, 'rb')
      # fp is not closed in this function as it is handed to the WSGI server
      # directly.
    except IOError:
      logging.warn('Requested non-existent filename %s', filename)
      return wrappers.Response(status=httplib.NOT_FOUND)

    wrapped_file = wsgi.wrap_file(request.environ, fp)
    return wrappers.Response(
        wrapped_file, direct_passthrough=True,
        mimetype=mime_type or mimetypes.guess_type(filename)[0])
  return serve_static_files
