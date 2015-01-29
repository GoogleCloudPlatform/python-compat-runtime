#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
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
#
"""VMEngines constants."""

# pylint: disable=g-import-not-at-top
try:
  from google.appengine.api import users
except ImportError:
  from google.appengine.api import users

# User used in applock and admin logs for background (Google-initiated)
# operations such periodic admin and autoscaling.
INTERNAL_ADMIN_USER = users.User(
    email='appengine-admin-noreply@google.com',
    _auth_domain='google.com',
    _user_id=None)

# TODO: This should be in shared_constants, since it's also used by AC.
# VMENGINES_TASK_QUEUE_NAME='vmengine'

PERIODIC_ADMIN_TASK_QUEUE_NAME = 'vmengine-periodic-admin'
DEFAULT_SERVING_PORT = 8080
DEFAULT_HEALTH_CHECK_PATH = '/_ah/health'
