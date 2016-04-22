"""Tests for the urlfetch API."""

import pytest
import time

from google.appengine.api import urlfetch


@pytest.fixture
def url():
  return 'http://www.google.com'

def test_urlfetch(url):
  resp = urlfetch.fetch(url)
  assert resp.status_code == 200
  assert resp.headers['content-length'] == str(len(resp.content))
