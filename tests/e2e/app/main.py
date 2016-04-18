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

import sys
import contextlib
from cStringIO import StringIO

import webapp2
import pytest


@contextlib.contextmanager
def capture():
    oldout, olderr = sys.stdout, sys.stderr
    try:
        out = StringIO()
        sys.stdout, sys.stderr = out, out
        yield out
    finally:
        sys.stdout, sys.stderr = oldout, olderr


class TestRunnerHandler(webapp2.RequestHandler):
    def get(self):
        with capture() as outf:
            result = pytest.main(['tests'])

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(outf.getvalue())
        if result != 0:
            self.response.status = 500


app = webapp2.WSGIApplication([
    ('/', TestRunnerHandler),
], debug=True)
