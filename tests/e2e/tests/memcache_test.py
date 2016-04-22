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

import time

from google.appengine.api import memcache

key1 = 'key1'
data1 = 'data1'
timeout = 2
timeout_tolerance = 2


def test_memcache():
    assert memcache.get(key1) is None
    memcache.set(key1, data1)
    assert memcache.get(key1) == data1
    assert memcache.set(key1, data1, timeout)
    time.sleep(timeout + timeout_tolerance)
    assert memcache.get(key1) is None
