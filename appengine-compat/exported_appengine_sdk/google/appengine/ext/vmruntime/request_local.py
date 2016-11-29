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


"""A Request-Local object.  Note, these objects are not thread-local."""



import UserDict

from google.appengine.ext.vmruntime import callback


class RequestLocal(object):
  """A replica of threading.local objects except across requests.

  RequestLocal objects, unlike thread-local objects, can and often are
  created outside the context of any requests.  In such scenarios, any
  attributes set outside a request are considered global attributes that can
  be accessed by any request.
  """

  def __getattribute__(self, name):
    request_id = callback.GetRequestId()
    my_dict = object.__getattribute__(self, '__dict__')


    if request_id and name in my_dict.setdefault(request_id, {}):
      return my_dict[request_id][name]


    return object.__getattribute__(self, name)

  def __setattr__(self, name, value):
    request_id = callback.GetRequestId()
    my_dict = object.__getattribute__(self, '__dict__')

    if request_id:
      if request_id in my_dict:
        my_dict[request_id][name] = value
      else:

        callback.SetRequestEndCallback(
            object.__getattribute__(self, '_cleanup'))
        my_dict[request_id] = {name: value}
    else:

      my_dict[name] = value

  def __delattr__(self, name):
    request_id = callback.GetRequestId()
    my_dict = object.__getattribute__(self, '__dict__')


    if not request_id:
      object.__delattr__(self, name)
      return


    if name in my_dict.setdefault(request_id, {}):
      del my_dict[request_id][name]
    elif object.__hasattr__(self, name):
      raise AttributeError('Cannot delete global attribute "%s"' % name)
    else:
      raise AttributeError('%s has no attribute "%s"' % (self, name))

  def _cleanup(self, req_id):
    my_dict = object.__getattribute__(self, '__dict__')
    del my_dict[req_id]


class RequestLocalDict(UserDict.IterableUserDict, RequestLocal):
  """A dictionary with request-local contents."""
