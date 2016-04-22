"""Tests for the search API."""

import pytest
import time

from google.appengine.api import search


@pytest.fixture
def index():
  index = search.Index(name='simple-index', namespace='')
  doc = search.Document(doc_id='test_id', fields=[
      search.TextField(name='body', value='hello world'),
  ])
  index.put(doc)
  return index


def test_basic_search(index):
  resp = index.search('hello')
  assert len(resp.results) == 1
  result = resp.results[0]
  assert result.doc_id == 'test_id'
  assert result.language == 'en'
  assert result.fields[0].value == 'hello world'
  assert result.fields[0].name == 'body'
