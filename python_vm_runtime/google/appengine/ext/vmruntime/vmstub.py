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





"""An APIProxy stub that communicates with VMEngine service bridges."""

from __future__ import with_statement



import imp
import logging
import multiprocessing.dummy
import os
import sys
import threading
import time
import traceback
import urlparse

from google.appengine.api import apiproxy_rpc
from google.appengine.api import apiproxy_stub_map
from google.appengine.ext.remote_api import remote_api_pb
from google.appengine.runtime import apiproxy_errors





requests = imp.load_module('requests_nologs', *imp.find_module('requests'))







logging.getLogger('requests_nologs').setLevel(logging.ERROR)


vmstub_logger = logging.getLogger(__name__)
vmstub_logger.setLevel(logging.INFO)

TICKET_HEADER = 'HTTP_X_APPENGINE_API_TICKET'
DEV_TICKET_HEADER = 'HTTP_X_APPENGINE_DEV_REQUEST_ID'
DAPPER_ENV_KEY = 'HTTP_X_GOOGLE_DAPPERTRACEINFO'
SERVICE_BRIDGE_HOST = 'appengine.googleapis.internal'
API_PORT = 10001
SERVICE_ENDPOINT_NAME = 'app-engine-apis'
APIHOST_METHOD = '/VMRemoteAPI.CallRemoteAPI'
PROXY_PATH = '/rpc_http'
DAPPER_HEADER = 'X-Google-DapperTraceInfo'
SERVICE_DEADLINE_HEADER = 'X-Google-RPC-Service-Deadline'
SERVICE_ENDPOINT_HEADER = 'X-Google-RPC-Service-Endpoint'
SERVICE_METHOD_HEADER = 'X-Google-RPC-Service-Method'
RPC_CONTENT_TYPE = 'application/octet-stream'
DEFAULT_TIMEOUT = 60

DEADLINE_DELTA_SECONDS = 1





MAX_CONCURRENT_API_CALLS = 100



_EXCEPTIONS_MAP = {
    remote_api_pb.RpcError.UNKNOWN: (
        apiproxy_errors.RPCFailedError,
        'The remote RPC to the application server failed for call %s.%s().'),
    remote_api_pb.RpcError.CALL_NOT_FOUND: (
        apiproxy_errors.CallNotFoundError,
        'The API package \'%s\' or call \'%s()\' was not found.'),
    remote_api_pb.RpcError.PARSE_ERROR: (
        apiproxy_errors.ArgumentError,
        'There was an error parsing arguments for API call %s.%s().'),
    remote_api_pb.RpcError.OVER_QUOTA: (
        apiproxy_errors.OverQuotaError,
        'The API call %s.%s() required more quota than is available.'),
    remote_api_pb.RpcError.REQUEST_TOO_LARGE: (
        apiproxy_errors.RequestTooLargeError,
        'The request to API call %s.%s() was too large.'),
    remote_api_pb.RpcError.CAPABILITY_DISABLED: (
        apiproxy_errors.CapabilityDisabledError,
        'The API call %s.%s() is temporarily disabled.'),
    remote_api_pb.RpcError.FEATURE_DISABLED: (
        apiproxy_errors.FeatureNotEnabledError,
        'The API call %s.%s() is currently not enabled.'),
    remote_api_pb.RpcError.RESPONSE_TOO_LARGE: (
        apiproxy_errors.ResponseTooLargeError,
        'The response from API call %s.%s() was too large.'),
    remote_api_pb.RpcError.CANCELLED: (
        apiproxy_errors.CancelledError,
        'The API call %s.%s() was explicitly cancelled.'),
    remote_api_pb.RpcError.DEADLINE_EXCEEDED: (
        apiproxy_errors.DeadlineExceededError,
        'The API call %s.%s() took too long to respond and was cancelled.')
}

_DEFAULT_EXCEPTION = _EXCEPTIONS_MAP[remote_api_pb.RpcError.UNKNOWN]

_DEADLINE_EXCEEDED_EXCEPTION = _EXCEPTIONS_MAP[
    remote_api_pb.RpcError.DEADLINE_EXCEEDED]





app_is_loaded = False


def CreateRequestPB(package, call, ticket, body):
  """Create a remote_api_pb.Request functionally.

  Args:
    package: String to set as the service name (package name).
    call: String to set as the method (API call name).
    ticket: String to set as the request ID (ticket).
    body: String to set as the request body.

  Returns:
    A remote_api_pb.Request.
  """

  request = remote_api_pb.Request()
  request.set_service_name(package)
  request.set_method(call)
  request.set_request_id(ticket)
  request.set_request(body)
  return request


def BodyAndHeadersForRequestPB(request_pb, deadline, dapper_trace=None):
  """Wrap a Request PB in an HTTP body and generate appropriate headers.

  Args:
    request_pb: An instance of remote_api_pb.Request.
    deadline: A deadline, in integer seconds, for the RPC response.
    dapper_trace: A string identifying the request for dapper tracing.

  Returns:
    A tuple of (body, headers) suitable for passing to requests.post().
  """


  body = request_pb.SerializeToString()

  headers = {
      SERVICE_DEADLINE_HEADER: deadline,
      SERVICE_ENDPOINT_HEADER: SERVICE_ENDPOINT_NAME,
      SERVICE_METHOD_HEADER: APIHOST_METHOD,
      'Content-type': RPC_CONTENT_TYPE,
  }


  if dapper_trace:
    headers[DAPPER_HEADER] = dapper_trace



  return body, headers


def EndpointURLForHostAndPort(api_host, api_port):
  """Return a proxied endpoint URL for a given host and port."""
  return urlparse.urlunparse(
      ('http', '%s:%s' % (api_host, api_port), PROXY_PATH,
       '', '', ''))


def MakeAPICallWithLogging(package, call, ticket, request_pb_body, endpoint_url,
                           deadline=DEFAULT_TIMEOUT, dapper_trace=None,
                           suppress_logging=False):
  """Make a post request to the API with logging.

  Args:
    package: String to set as the service name (package name).
    call: String to set as the method (API call name).
    ticket: String to set as the request ID (ticket).
    request_pb_body: String to set as the request body.
    endpoint_url: The service bridge endpoint to target.
    deadline: A deadline, in integer seconds, for the RPC response.
    dapper_trace: A string identifying the request for dapper tracing.
    suppress_logging: True if logging should not be performed, for instance
        to avoid infinite loops during calls to logservice.

  Returns:
    A requests.Response object containing the service bridge's response.
  """


  request_pb = CreateRequestPB(package, call, ticket, request_pb_body)


  body, headers = BodyAndHeadersForRequestPB(request_pb, deadline, dapper_trace)

  start_time = time.clock()

  try:
    response = requests.post(url=endpoint_url,
                             headers=headers,
                             data=body,
                             timeout=DEADLINE_DELTA_SECONDS + deadline)
  except Exception as e:
    if not suppress_logging:
      ms = int((time.clock() - start_time) / 1000)
      vmstub_logger.exception(
          'Exception during service bridge API call to package: %s, call: %s, '
          'of size: %s bytes. Took %s ms. %s', package, call,
          len(request_pb_body), ms, e)

    raise type(e)(''.join(traceback.format_exception(*sys.exc_info())))
  else:
    if not suppress_logging:
      ms = int((time.clock() - start_time) / 1000)
      vmstub_logger.info(
          'Service bridge API call to package: %s, call: %s, of size: %s '
          'complete. Service bridge status code: %s; response '
          'content-length: %s. Took %s ms.', package, call,
          len(request_pb_body), response.status_code,
          response.headers.get('content-length'), ms)

  return response


class SyncResult(object):
  """A class that emulates multiprocessing.AsyncResult.

  This allows us to use the same API for getting results from both sync and
  async API calls.
  """

  def __init__(self, value, success):
    self.value = value
    self.success = success

  def get(self):
    if self.success:
      return self.value
    else:
      raise self.value






class VMEngineRPC(apiproxy_rpc.RPC):
  """A class representing an RPC to a remote server."""

  def _ErrorException(self, exception_class, error_details):
    return exception_class(error_details % (self.package, self.call))

  def  _TranslateToError(self, response):
    """Translates a failed APIResponse into an exception."""


    if response.has_rpc_error():
      code = response.rpc_error().code()
      detail = response.rpc_error().detail()
      exception_type, msg = _EXCEPTIONS_MAP.get(code, _DEFAULT_EXCEPTION)

      if detail and exception_type == _DEFAULT_EXCEPTION:
        msg = '%s -- Additional details from server: %s' % (msg, detail)
      raise self._ErrorException(exception_type, msg)


    raise apiproxy_errors.ApplicationError(
        response.application_error().code(),
        response.application_error().detail())

  def _MakeCallImpl(self):
    """Makes an asynchronous API call over the service bridge.

    For this to work the following must be set:
      self.package: the API package name;
      self.call: the name of the API call/method to invoke;
      self.request: the API request body as a serialized protocol buffer.

    The actual API call is made by requests.post via a thread pool
    (multiprocessing.dummy.Pool). The thread pool restricts the number of
    concurrent requests to MAX_CONCURRENT_API_CALLS, so this method will
    block if that limit is exceeded, until other asynchronous calls resolve.

    If the main thread holds the import lock, waiting on thread work can cause
    a deadlock:
    https://docs.python.org/2/library/threading.html#importing-in-threaded-code

    Therefore, we try to detect this error case and fall back to sync calls.
    """
    assert self._state == apiproxy_rpc.RPC.IDLE, self._state

    self.lock = threading.Lock()
    self.event = threading.Event()


    if VMStub.ShouldUseRequestSecurityTicketForThread():


      ticket = os.environ.get(TICKET_HEADER,
                              os.environ.get(DEV_TICKET_HEADER,
                                             self.stub.DefaultTicket()))
    else:
      ticket = self.stub.DefaultTicket()

    self._state = apiproxy_rpc.RPC.RUNNING

    endpoint_url = EndpointURLForHostAndPort(
        os.environ.get('API_HOST', SERVICE_BRIDGE_HOST),
        os.environ.get('API_PORT', API_PORT))

    request_pb_body = self.request.SerializeToString()







    suppress_logging = self.package == 'logservice' and self.call == 'Flush'



    if imp.lock_held() and not app_is_loaded:
      try:
        value = MakeAPICallWithLogging(
            self.package, self.call, ticket, request_pb_body, endpoint_url,
            deadline=self.deadline or DEFAULT_TIMEOUT,
            dapper_trace=os.environ.get(DAPPER_ENV_KEY),
            suppress_logging=suppress_logging)
        success = True
      except Exception as e:
        value = e
        success = False
      self._result_future = SyncResult(value, success)


    else:



      self._result_future = self.stub.thread_pool.apply_async(
          MakeAPICallWithLogging,
          args=[self.package, self.call, ticket, request_pb_body, endpoint_url],
          kwds={'deadline': self.deadline or DEFAULT_TIMEOUT,
                'dapper_trace': os.environ.get(DAPPER_ENV_KEY),
                'suppress_logging': suppress_logging}
          )

  def _WaitImpl(self):





    try:
      already_finishing = False
      with self.lock:


        if self._state == apiproxy_rpc.RPC.FINISHING:
          already_finishing = True
        else:
          self._state = apiproxy_rpc.RPC.FINISHING
      if already_finishing:
        self.event.wait()
        return True


      try:

        response = self._result_future.get()

        if response.status_code != requests.codes.ok:
          raise apiproxy_errors.RPCFailedError(
              'Proxy returned HTTP status %s %s' %
              (response.status_code, response.reason))
      except requests.exceptions.Timeout:






        raise self._ErrorException(*_DEADLINE_EXCEEDED_EXCEPTION)
      except requests.exceptions.RequestException:

        raise self._ErrorException(*_DEFAULT_EXCEPTION)


      parsed_response = remote_api_pb.Response(response.content)


      if (parsed_response.has_application_error() or
          parsed_response.has_rpc_error()):

        raise self._TranslateToError(parsed_response)


      self.response.ParseFromString(parsed_response.response())

    except Exception:


      _, exc, tb = sys.exc_info()
      self._exception = exc
      self._traceback = tb

    try:
      self._Callback()
      return True
    finally:

      self.event.set()


class _UseRequestSecurityTicketLocal(threading.local):
  """Thread local holding if the default ticket should always be used."""

  def __init__(self):
    super(_UseRequestSecurityTicketLocal, self).__init__()
    self.use_ticket_header_value = False


class VMStub(object):
  """A stub for calling services through a VM service bridge.

  You can use this to stub out any service that the remote server supports.
  """


  _USE_REQUEST_SECURITY_TICKET_LOCAL = _UseRequestSecurityTicketLocal()

  @classmethod
  def SetUseRequestSecurityTicketForThread(cls, value):
    """Sets if the in environment security ticket should be used.

    Security tickets are set in the os.environ, which gets inherited by a
    child thread.  Child threads should not use the security ticket of their
    parent by default, because once the parent thread returns and the request
    is complete, the security ticket is no longer valid.

    Args:
      value: Boolean value describing if we should use the security ticket.
    """
    cls._USE_REQUEST_SECURITY_TICKET_LOCAL.use_ticket_header_value = value

  @classmethod
  def ShouldUseRequestSecurityTicketForThread(cls):
    """Gets if thie security ticket should be used for this thread."""
    return cls._USE_REQUEST_SECURITY_TICKET_LOCAL.use_ticket_header_value


  def __init__(self, default_ticket=None):

    self.thread_pool = multiprocessing.dummy.Pool(MAX_CONCURRENT_API_CALLS)
    self.default_ticket = default_ticket


  def DefaultTicket(self):
    return self.default_ticket or os.environ['DEFAULT_TICKET']

  def MakeSyncCall(self, service, call, request, response):
    """Make a synchronous API call.

    Args:
      service: The name of the service you are trying to use.
      call: The name of the method.
      request: The request protocol buffer
      response: The response protocol buffer to be filled.
    """
    rpc = self.CreateRPC()
    rpc.MakeCall(service, call, request, response)
    rpc.Wait()
    rpc.CheckSuccess()

  def CreateRPC(self):
    """Create a new RPC object."""
    return VMEngineRPC(stub=self)


def Register(stub):
  """Insert stubs so App Engine services are accessed via the service bridge."""
  apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap(stub)
