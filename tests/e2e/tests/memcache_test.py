"""Tests for the memcache API."""

import pytest
import time

from google.appengine.api import memcache


@pytest.fixture
def defaults():
  memcache.flush_all()
  return {
      'client': memcache._CLIENT,
      'mapping': {
          'key1', 'data1',
          'key2', 'data2',
          'key3', 'data3',
      },
      'timeout': 2,
      'timeout_tolerance': 2,
      'namespace1': 'foo',
      'namespace2': 'bar',
      'default_range': 10,
      'default_incr_start': 1,
      'default_decr_start': 1000,
      'default_delta': 10,
  }


def test_memcache(defaults):
  assert memcache.get('key1') == None
  memcache.set('key1', 'data1')
  assert memcache.get('key1') == 'data1'
  assert memcache.set('key1', 'data1', defaults['timeout'])
  time.sleep(defaults['timeout'] + defaults['timeout_tolerance'])
  assert memcache.get('key1') == None
