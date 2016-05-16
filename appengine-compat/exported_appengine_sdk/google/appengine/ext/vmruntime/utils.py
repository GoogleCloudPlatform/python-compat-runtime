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


"""Utility functions for python vm runtimes."""



import thread
import threading


def PatchStartNewThread(thread_module=thread, threading_module=threading):
  """Use custom version of start_new_thread."""
  thread_module.start_new_thread = _MakeStartNewThread(
      thread_module.start_new_thread)
  reload(threading_module)


def _MakeStartNewThread(base_start_new_thread):
  """Replaces start_new_thread to register itself with the parent's request.

  Args:
    base_start_new_thread: The thread.start_new_thread function.

  Returns:
    Replacement for start_new_thread.
  """

  def StartNewThread(target, args, kw=None):
    """A replacement for thread.start_new_thread.

    Ensures this child thread will be associated with the correct request ID.

    Args:
      target: Function to be called.
      args:  Args to be passed in.
      kw: Key word arguments to be passed in.

    Returns:
      Same as thread.start_new_thread
    """
    req_id = GetRequestId()
    if kw is None:
      kw = {}
    def Run():
      SetRequestId(req_id)
      try:
        target(*args, **kw)
      finally:
        DeleteRequestId(threading.current_thread().ident)
    return base_start_new_thread(Run, ())
  return StartNewThread


_req_by_threads = {}


def GetRequestId():
  """Returns a unique ID using the cloud trace ID.

  Only threads (or child threads) from user requests should have a request ID.
  Other threads, such as initialization threads, do not have a request ID.

  Returns:
    The request ID.
  """
  return _req_by_threads.setdefault(threading.current_thread().ident, None)


def SetRequestId(req_id):
  """Places the current thread in the context of the given request.

  Args:
    req_id: The request ID.
  """
  _req_by_threads[threading.current_thread().ident] = req_id


def DeleteRequestId(thread_id):
  """Deletes the request ID associated with the thread.

  Used by main request thread but also by child threads.

  Args:
    thread_id: The thread ID that will be deleted.
  """
  del _req_by_threads[thread_id]


def InsideRequest():
  """True if we have a request ID."""
  return GetRequestId() is not None

