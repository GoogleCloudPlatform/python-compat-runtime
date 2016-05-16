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


"""Callbacks the runtime invokes when requests end."""



from google.appengine.ext.vmruntime import utils

_callback_storage = {}


def SetRequestEndCallback(callback):
  """Stores a callback by the request ID.

  The request ID currently uses the cloud trace ID.

  Args:
    callback: A zero-argument callable whose return value is unused.
  """
  req_id = utils.GetRequestId()




  if req_id:
    _callback_storage.setdefault(req_id, []).append(callback)


def InvokeCallbacks():
  """Invokes the callbacks associated with the current request ID."""
  req_id = utils.GetRequestId()
  if req_id in _callback_storage:
    for callback in _callback_storage[req_id]:
      callback(req_id)
    del _callback_storage[req_id]
