"""E2E test for Users API."""
import pytest

from google.appengine.api import users


@pytest.fixture
def user():
  return users.get_current_user()

def test_current_user(user):
  assert user == None
