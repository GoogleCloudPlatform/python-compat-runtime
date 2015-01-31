import unittest
from mock import patch, MagicMock

from werkzeug.test import Client
from werkzeug.wrappers import Request, Response

from google.appengine.api import appinfo

FAKE_HANDLERS = [
    appinfo.URLMap(url='/hello', script='wsgi_test.hello_world'),
    appinfo.URLMap(url='/failure', script='wsgi_test.nonexistent_function')]
HELLO_STRING = 'Hello World!'

@Request.application
def hello_world(request):
  return Response(HELLO_STRING)

class MetaAppTestCase(unittest.TestCase):

  def setUp(self):
    # Pre-import modules to patch them in advance.
    from google.appengine.ext.vmruntime import vmconfig

    # Instantiate an app with a simple fake configuration.
    with patch('wsgi_utils.get_module_config_filename'):
      with patch('wsgi_utils.get_module_config', return_value=MagicMock(handlers=FAKE_HANDLERS)):
        with patch('google.appengine.ext.vmruntime.vmconfig.BuildVmAppengineEnvConfig', default_ticket="0"):
          import wsgi
          self.app = wsgi.meta_app
    self.client = Client(self.app, Response)

  def test_hello(self):
    response = self.client.get('/hello')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data, HELLO_STRING)

  def test_failure(self):
    response = self.client.get('/failure')
    self.assertEqual(response.status_code, 500)

  def test_notfound(self):
    response = self.client.get('/notfound')
    self.assertEqual(response.status_code, 404)
