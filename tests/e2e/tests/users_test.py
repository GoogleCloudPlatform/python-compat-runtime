from google.appengine.api import users
import pytest

user = users.get_current_user()

def test_current_user():
  assert user == None
