import os
import pytest

from google.appengine.ext.ndb import model, tasklets

class Employee(model.Model):
  name = model.StringProperty()
  age = model.IntegerProperty()


@pytest.fixture
def ctx():
  ctx = tasklets.get_context()
  ctx.set_cache_policy(False)
  ctx.set_memcache_policy(False)
  return ctx

def test_basics(ctx):
  worker = Employee(name='Alice', age=55)
  key = worker.put()
  same_worker = key.get()
  assert worker == same_worker
