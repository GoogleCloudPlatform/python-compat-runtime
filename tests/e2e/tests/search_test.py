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

from google.appengine.api import search
import pytest


@pytest.fixture
def index():
    index = search.Index(name='simple-index', namespace='')
    doc = search.Document(
        doc_id='test_id',
        fields=[
            search.TextField(
                name='body',
                value='hello world'),
        ])
    index.put(doc)

    # Search is eventually consistent, so sleep for 2 seconds before continuing
    time.sleep(2)

    return index


def test_basic_search(index):
    resp = index.search('hello')
    assert len(resp.results) == 1
    result = resp.results[0]
    assert result.doc_id == 'test_id'
    assert result.language == 'en'
    assert result.fields[0].value == 'hello world'
    assert result.fields[0].name == 'body'
