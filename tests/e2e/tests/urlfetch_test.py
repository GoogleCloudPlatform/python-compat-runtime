from google.appengine.api import urlfetch
import pytest
import time

url = 'http://www.google.com'

def test_urlfetch():
  resp = urlfetch.fetch(url)
  assert resp.status_code == 200
  assert resp.headers['content-length'] == str(len(resp.content))
