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



"""An API for creating background threads.

Background threads created using this API do not inherit the context
of their creator and do not need to end before the creator request
completes.

NOTE: This is just provided for compatibility.  You might as well just
use the threading module directly.
"""

from __future__ import with_statement






__all__ = ['start_new_background_thread',
           'BackgroundThread',
           'Error',
           'FrontendsNotSupported',
           'BackgroundThreadLimitReachedError',
          ]

import os
import thread
import threading

from google.appengine.api.logservice import logservice
from google.appengine.runtime import request_environment



_original_start_new_thread = thread.start_new_thread


_ENVIRON_KEYS = [
    'APPENGINE_RUNTIME',
    'APPLICATION_ID',
    'BACKEND_ID',
    'CURRENT_VERSION_ID',
    'DATACENTER',
    'DEFAULT_VERSION_HOSTNAME',
    'INSTANCE_ID',
    'SERVER_SOFTWARE',
    'TZ',
    ]



_original_environ = dict(os.environ)



_filtered_environ = {}


def _capture_environ():
  global _filtered_environ
  _filtered_environ = dict((k, v)
                           for k, v in os.environ.iteritems()
                           if k in _ENVIRON_KEYS)


  _filtered_environ['AUTH_DOMAIN'] = 'example.com'



class Error(Exception):
  """Base exception class for this module."""


class FrontendsNotSupported(Error):
  """Error raised when a background thread is requested on a front end."""


class BackgroundThreadLimitReachedError(Error):
  """Error raised when no further active background threads can be created."""


def start_new_background_thread(target, args, kwargs=None):
  """Starts a new background thread.

  Creates a new background thread which will call target(*args, **kwargs).

  Args:
    target: A callable for the new thread to run.
    args: Position arguments to be passed to target.
    kwargs: Keyword arguments to be passed to target.

  Returns:
    The thread ID of the background thread.
  """
  _capture_environ()
  _original_start_new_thread(_bootstrap, (target, args, kwargs))


class BackgroundThread(threading.Thread):
  """A threading.Thread subclass for background threads."""

  def start(self):
    """Starts this background thread."""
    _capture_environ()

    if not self._Thread__initialized:
      raise RuntimeError('thread.__init__() not called')
    if self._Thread__started.is_set():
      raise RuntimeError('threads can only be started once')
    with threading._active_limbo_lock:
      threading._limbo[self] = self
    try:

      start_new_background_thread(self._Thread__bootstrap, ())
    except Exception:
      with threading._active_limbo_lock:
        del threading._limbo[self]
      raise
    self._Thread__started.wait()


def _bootstrap(target, args, kwargs=None):
  """Helper to start a thread."""
  if kwargs is None:
    kwargs = {}
  errors = logservice.LogsBuffer()
  environ = dict(_original_environ)
  if _filtered_environ:
    environ.update(_filtered_environ)
  try:
    request_environment.current_request.Init(errors, environ)
    target(*args, **kwargs)
  finally:
    request_environment.current_request.Reset()
