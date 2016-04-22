from google.appengine.api import memcache
import pytest
import time

key1 = 'key1'
data1 = 'data1'
timeout = 2
timeout_tolerance = 2

def test_memcache():
  assert memcache.get(key1) == None
  memcache.set(key1, data1)
  assert memcache.get(key1) == data1
  assert memcache.set(key1, data1, timeout)
  time.sleep(timeout + timeout_tolerance)
  assert memcache.get(key1) == None
