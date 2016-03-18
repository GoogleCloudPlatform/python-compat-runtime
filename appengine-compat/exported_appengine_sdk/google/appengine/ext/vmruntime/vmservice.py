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
"""Service running an App engine app on a Compute Engine VM."""


from __future__ import with_statement
import logging
import SocketServer
import sys
import traceback
from wsgiref import simple_server

from google.appengine.api import appinfo_includes
from google.appengine.ext.vmruntime import meta_app
from google.appengine.ext.vmruntime import middlewares
from google.appengine.ext.vmruntime import vmconfig
from google.appengine.ext.vmruntime import vmstub



try:
  import googleclouddebugger
except ImportError:
  pass

LISTENING_HOST = '0.0.0.0'
HTTP_PORT = 8080


class VmRuntimeServer(object):
  """Server for an AppEngine VMRuntime app."""

  def __init__(self, host, port, app, appinfo_external):
    """Constructor.

    Args:
      host: The (string) host to bind to, e.g. 'localhost' or '0.0.0.0'.
      port: The (integer) port to bind to.
      app: The WSGI app to serve.
      appinfo_external: The AppInfoExternal for the user app we are running.
    """
    self._host, self._port = host, port
    self._app = app
    self._appinfo_external = appinfo_external
    self._server = self.CreateServer()
    logging.info('Creating server on %s:%d', self._host, self._port)

  def RunForever(self):
    """Serves this Server's application forever."""
    raise NotImplementedError()

  def CreateServer(self):
    """Returns a WSGIServer for self._app."""
    raise NotImplementedError()


class VmRuntimeWSGIRefServer(VmRuntimeServer):

  def CreateServer(self):
    return simple_server.make_server(
        self._host, self._port, self._app,
        server_class=self._ThreadingWSGIServer)

  def RunForever(self):
    try:
      self._server.serve_forever()
    except:
      logging.error('Could not start server on %s:%s.', self._host, self._port)
      raise

  class _ThreadingWSGIServer(SocketServer.ThreadingMixIn,
                             simple_server.WSGIServer):
    daemon_threads = True


class VmRuntimeCherryPyServer(VmRuntimeServer):

  def CreateServer(self):

    from cherrypy.wsgiserver import wsgiserver2



    wsgiserver2.socket_error_eintr.append(512)
    return wsgiserver2.CherryPyWSGIServer(
        (self._host, self._port), self._app,
        numthreads=middlewares.MAX_CONCURRENT_REQUESTS,




        request_queue_size=middlewares.MAX_CONCURRENT_REQUESTS)

  def RunForever(self):
    try:
      self._server.start()
    except:
      logging.error('Could not start server on %s:%s.', self._host, self._port)
      raise


class VmService(object):
  """Class to create and run the service."""

  server_class = VmRuntimeWSGIRefServer

  server_class = VmRuntimeCherryPyServer

  def __init__(self, filename, host, port):
    self.filename = filename
    self.host = host
    self.port = port
    self.server = None

  def CreateServer(self):

    with open(self.filename) as stream:
      appinfo_external = appinfo_includes.Parse(stream)

    appengine_config = vmconfig.BuildVmAppengineEnvConfig()
    vmstub.Register(vmstub.VMStub(appengine_config.default_ticket))








    if 'googleclouddebugger' in sys.modules:
      try:
        googleclouddebugger.AttachDebugger()
      except Exception as e:
        logging.warn('Exception while initializing Cloud Debugger: %s',
                     traceback.format_exc(e))








    try:
      import appengine_config as user_appengine_config
    except ImportError:
      pass

    app = meta_app.FullyWrappedApp(appinfo_external, appengine_config)
    self.server = self.server_class(self.host, self.port, app,
                                    appinfo_external)
    logging.info('Configured server on %s:%s', self.host, self.port)

  def StartServer(self):
    assert self.server
    self.server.RunForever()


def CreateAndRunService(config_filename):
  """Helper called from vmboot.main() to create and run the service."""
  service = VmService(config_filename, LISTENING_HOST, HTTP_PORT)
  service.CreateServer()
  service.StartServer()
