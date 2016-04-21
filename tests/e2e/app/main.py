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

from cStringIO import StringIO
from gcloud import storage

import contextlib
import pytest
import os
import shutil
import signal
import sys
import webapp2

# Configure this environment variable via app.yaml.in.
# Cut off the 'gs://' portion of the name.
GCLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET'][5:]


@contextlib.contextmanager
def capture():
    oldout, olderr = sys.stdout, sys.stderr
    try:
        out = StringIO()
        sys.stdout, sys.stderr = out, out
        yield out
    finally:
        sys.stdout, sys.stderr = oldout, olderr

class RefreshHandler(webapp2.RequestHandler):

  def get(self):
      # Set up test directory.
      if os.path.isdir('tests'):
          shutil.rmtree('tests')
      os.mkdir('tests')

      # Refresh the tests from cloud storage.
      bucket = storage.Client().get_bucket(GCLOUD_STORAGE_BUCKET)
      blob_iter = bucket.list_blobs()
      for blob in blob_iter:
          blob.download_to_filename('tests/%s' % blob.name)

      # Tell Gunicorn to refresh this process so that our modules
      # will be refreshed with the new files.  The gunicorn process
      # is stored in gunicorn_pid.txt.
      with open('gunicorn_pid.txt') as f:
          for line in f:
              pid = int(line)

      os.kill(pid, signal.SIGHUP)



class TestRunnerHandler(webapp2.RequestHandler):

    def get(self):
        # Run the tests.
        with capture() as outf:
            result = pytest.main(['tests'])

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(outf.getvalue())
        if result != 0:
            self.response.status = 500




app = webapp2.WSGIApplication([
    ('/refresh', RefreshHandler),
    ('/test', TestRunnerHandler),
], debug=True)
