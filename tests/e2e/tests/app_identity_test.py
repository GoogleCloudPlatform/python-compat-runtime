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

from google.appengine.api import app_identity


def test_get_service_account_name():
    assert app_identity.get_service_account_name()


def test_get_application_id():
    assert app_identity.get_application_id()


def test_get_default_version_hostname():
    app_id = app_identity.get_application_id()
    hostname = app_identity.get_default_version_hostname()
    assert hostname
    assert app_id in hostname


def test_get_access_token():
    token = app_identity.get_access_token(
        ['https://www.googleapis.com/auth/userinfo.email'])
    assert token
    # TODO: Verify token with tokeninfo endpoint.


def test_get_default_gcs_bucket_name():
    assert app_identity.get_default_version_hostname()


def test_sign_blob():
    cleartext = 'Curiouser and curiouser!'
    key_name, signature = app_identity.sign_blob(cleartext)
    assert key_name
    assert signature
