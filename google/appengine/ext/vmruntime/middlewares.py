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
"""Methods for gluing a user's application into the GAE environment."""

import functools
import logging
import os
import sys
import threading
import time
import traceback
import urllib2

from google.appengine.api import logservice
from google.appengine.runtime import request_environment


LOG_FLUSH_COUNTER_HEADER = 'X-AppEngine-Log-Flush-Count'


MAX_CONCURRENT_REQUESTS = 501

REQUEST_LOG_FILE = '/var/log/app_engine/request.log'


def PatchLoggingMethods(app):
  """Middleware for monkey patching logservice handling.

  This method:
    1) Sets request_environment.current_request.errors to a new instance
       of a LogsBuffer. See initialize.InitializeApiLogging for where
       this gets used.
    2) Patches logservice.Flush with a thin wrapper that counts logflush calls.
       We send this counter to the AppServer so that the appserver knows
       if it must wait for outstanding logflush calls.

  Args:
    app: (callable) a WSGI app per PEP 333.

  Returns:
    A wrapped <app>, which is also a valid WSGI app.
  """








  def LogWrapper(wsgi_env, start_response):
    """The middleware WSGI app."""

    errors = logservice.LogsBuffer()

    environ = request_environment.current_request.environ
    request_environment.current_request.Init(errors, environ)

    original_flush = errors._flush
    request_environment.current_request.flush_count = 0



    def FlushAndCount():
      """Count how many times we have flushed and then flush the request."""
      try:
        request_environment.current_request.flush_count += 1
      except AttributeError:




        request_environment.current_request.flush_count = 1
      original_flush()

    errors._flush = FlushAndCount
    return app(wsgi_env, start_response)

  return LogWrapper


def LogFlushCounter(app):
  """WSGI middleware wrapper that counts the number of logservice.Flush calls.

  This adds a header to the HTTP response representing the number of flushes
  made during this request.

  Since a logging API call can be made at any time, we have to subvert
  the efficiency of WSGI streaming by deferring the header creation (and
  therefore response start) until all of the response data has been written.

  Args:
    app: (callable) a WSGI app per PEP 333.

  Returns:
    A wrapped <app>, which is also a valid WSGI app.
  """

  def AppWrapper(env, start_response):
    """Wrapper for <app>."""





    status_list = []
    headers_list = []
    exc_info_list = []
    write_buffer_list = []

    def MyWrite(buf, s):
      if s is not None:
        buf.append(s)

    def DeferredStartResponse(status, headers, exc_info=None):
      status_list.append(status)
      headers_list.append(headers)
      exc_info_list.append(exc_info)
      buf = []
      write_buffer_list.append(buf)
      return functools.partial(MyWrite, buf)

    retval = []
    result = app(env, DeferredStartResponse)
    if result is not None:
      for value in result:
        retval.append(value)






    if logservice.log_buffer_bytes():
      logservice.flush()


    flush_count = str(getattr(
        request_environment.current_request, 'flush_count', -1))
    if headers_list:
      headers_list[0].append((LOG_FLUSH_COUNTER_HEADER, flush_count))
    for status, headers, exc_info, write_buffer in zip(
        status_list, headers_list, exc_info_list, write_buffer_list):
      write_fn = start_response(status, headers, exc_info)
      if write_buffer:
        write_fn(''.join(write_buffer))
        write_buffer = []
    return retval

  return AppWrapper


def RequestQueueingMiddleware(app, appinfo_external):
  """Throttles requests per max_concurrent_requests, or a default value."""
  if appinfo_external.threadsafe:
    serving_pool_size = MAX_CONCURRENT_REQUESTS
  else:
    serving_pool_size = 1


  queue_size = serving_pool_size + MAX_CONCURRENT_REQUESTS



  serving_sem = threading.Semaphore(serving_pool_size)
  queue_sem = threading.Semaphore(queue_size)

  def QueueingWrapper(wsgi_env, start_response):
    path = wsgi_env.get('PATH_INFO')
    if path != '/_ah/health':

      got_queueing = queue_sem.acquire(blocking=False)
      if not got_queueing:

        response_headers = [('content-type', 'text/plain')]
        start_response('503 Service Unavailable', response_headers)
        return ['Server is too busy, please try again later.']
      else:
        serving_sem.acquire(blocking=True)
        try:
          return app(wsgi_env, start_response)
        finally:
          queue_sem.release()
          serving_sem.release()
    else:

      return app(wsgi_env, start_response)

  return QueueingWrapper




def RequestLoggingMiddleware(app):
  """Logs the HTTP request for the given app."""

  def _SetupRequestLogger(logger):


    logger.propagate = False
    logger.handlers = []
    handler = logging.FileHandler(REQUEST_LOG_FILE)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    return logger

  request_logger = _SetupRequestLogger(logging.getLogger(
      'google.appengine.ext.vmruntime.request_logger'))

  def LogRequestWrapper(wsgi_env, start_response):
    """The middleware WSGI app."""
    client = wsgi_env.get('REMOTE_ADDR', '-')
    method = wsgi_env.get('REQUEST_METHOD', '-')
    path = wsgi_env.get('PATH_INFO', '-')
    stamp = time.strftime('%Y-%m-%d %H:%M:%S]')
    log_entries = [stamp, client, method, path]


    def StartResponseWrapper(status, *args, **kwargs):
      log_entries.append(status)
      request_logger.info(' '.join(log_entries))
      return start_response(status, *args, **kwargs)


    return app(wsgi_env, StartResponseWrapper)


  return LogRequestWrapper


def ErrorLoggingMiddleware(app):
  """Catch and log unhandled errors for the given app."""

  def ErrorLoggingWrapper(wsgi_env, start_response):
    """Wrap the application into an error handler."""
    try:
      return app(wsgi_env, start_response)
    except:








      log_message = traceback.format_exception(
          sys.exc_info()[0],
          sys.exc_info()[1],
          sys.exc_info()[2])

      logging.error(''.join(log_message))
      raise

  return ErrorLoggingWrapper


def WsgiEnvSettingMiddleware(app, appinfo_external):
  """Modify the wsgi env variable according to this application."""

  def SetWsgiEnv(wsgi_env, start_response):
    """The middleware WSGI app."""
    wsgi_env['wsgi.multithread'] = appinfo_external.threadsafe
    return app(wsgi_env, start_response)

  return SetWsgiEnv


def _MetadataGetter(key):
  return urllib2.urlopen(
      'http://metadata/0.1/meta-data/attributes/' + key).read()



def OsEnvSetupMiddleware(app, metadata_getter=None):
  """Patch os.environ to be thread local, and stamp it with default values.

  When this function is called, we remember the values of os.environ. When the
  wrapped inner function (i.e. the WSGI middleware) is called, we patch
  os.environ to be thread local, and we fill in the remembered values. Per
  request, we also merge the WSGI environment with os.environ.

  Args:
    app: The WSGI app to wrap.
    metadata_getter: Function that takes a key and returns this VMs metadata for
      that key. If None, we'll use the production value.

  Returns:
    The wrapped app, also a WSGI app.
  """
  metadata_getter = metadata_getter or _MetadataGetter

  appid = os.environ.get('GAE_LONG_APP_ID') or metadata_getter('gae_project')
  partition = (os.environ.get('GAE_PARTITION')
               or metadata_getter('gae_partition'))
  module = (os.environ.get('GAE_MODULE_NAME') or
            metadata_getter('gae_backend_name'))


  instance = (os.environ.get('GAE_MODULE_INSTANCE') or
              metadata_getter('gae_backend_instance'))

  major_version = os.environ.get('GAE_MODULE_VERSION')
  if not major_version:


    version = metadata_getter('gae_backend_version')



    major_version = version.rsplit('_')[0]

  minor_version = os.environ.get('GAE_MINOR_VERSION')
  if not minor_version:





    pwd = os.getcwd()
    base = os.path.basename(pwd)
    minor_version = base.rsplit('-', 1)[-1]



  escaped_appid = appid.replace(':', '_').replace('.', '_')
  default_ticket = '%s/%s.%s.%s' % (
      escaped_appid, module, major_version, instance)



  server_software = os.environ.get('SERVER_SOFTWARE')




  original_environ = dict(os.environ)

  def PatchEnv(wsgi_env, start_response):
    """The middleware WSGI app."""
    request_environment.PatchOsEnviron()
    os.environ.clear()
    os.environ.update(original_environ)
    for key, val in wsgi_env.iteritems():
      if isinstance(val, basestring):
        os.environ[key] = val

    os.environ['SERVER_SOFTWARE'] = server_software
    os.environ['APPENGINE_RUNTIME'] = 'python27'
    os.environ['APPLICATION_ID'] = '%s~%s' % (partition, appid)
    os.environ['INSTANCE_ID'] = instance
    os.environ['BACKEND_ID'] = major_version
    os.environ['CURRENT_MODULE_ID'] = module
    os.environ['CURRENT_VERSION_ID'] = '%s.%s' % (major_version, minor_version)
    os.environ['DEFAULT_TICKET'] = default_ticket
    return app(wsgi_env, start_response)

  return PatchEnv


def FixServerEnvVarsMiddleware(app):
  """Adjust SERVER_NAME and SERVER_PORT env vars to hide service bridge."""

  def FixVars(wsgi_env, start_response):
    """The wrapped app."""






    if 'HTTP_HOST' in os.environ:
      os.environ['SERVER_NAME'] = os.environ['HTTP_HOST']



    if 'HTTPS' in os.environ:
      https = os.environ['HTTPS']
      if https == 'off':
        os.environ['SERVER_PORT'] = '80'
      elif https == 'on':
        os.environ['SERVER_PORT'] = '443'
      else:
        logging.warning('Unrecognized value for HTTPS ( ' + https +
                        '), won\'t modify SERVER_PORT')

    return app(wsgi_env, start_response)

  return FixVars
