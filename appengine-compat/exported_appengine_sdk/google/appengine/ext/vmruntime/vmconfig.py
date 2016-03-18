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
"""Logic to fetch configuration variables about the vm's environment."""

import collections
import os
import urllib2

_METADATA_BASE_PATH = 'http://metadata/computeMetadata/v1/instance/attributes'


def _MetadataGetter(key):
  """Default metadata getter.

  Args:
    key: The metadata key.

  Returns:
    The metadata value as a string.
  """
  req = urllib2.Request('%s/%s' % (_METADATA_BASE_PATH, key))
  req.add_header('Metadata-Flavor', 'Google')
  return urllib2.urlopen(req).read()


VmAppengineEnvConfig = collections.namedtuple(
    'VmAppengineEnvConfig',
    ['appid', 'partition', 'module',
     'major_version', 'minor_version', 'instance',
     'default_ticket', 'server_software',
     'appengine_hostname'])


def BuildVmAppengineEnvConfig():
  """Build a VmAppengineEnvConfig based on the env and metadata."""
  appid = os.environ.get('GAE_LONG_APP_ID')
  partition = os.environ.get('GAE_PARTITION')
  module = os.environ.get('GAE_MODULE_NAME')
  major_version = os.environ.get('GAE_MODULE_VERSION')
  minor_version = os.environ.get('GAE_MINOR_VERSION')
  appengine_hostname = os.environ.get('GAE_APPENGINE_HOSTNAME')



  instance = (os.environ.get('GAE_MODULE_INSTANCE') or
              _MetadataGetter('gae_backend_instance'))


  escaped_appid = appid.replace(':', '_').replace('.', '_')
  default_ticket = '%s/%s.%s.%s' % (
      escaped_appid, module, major_version, instance)



  server_software = os.environ.get('SERVER_SOFTWARE')

  return VmAppengineEnvConfig(appid=appid,
                              partition=partition,
                              module=module,
                              major_version=major_version,
                              minor_version=minor_version,
                              instance=instance,
                              default_ticket=default_ticket,
                              server_software=server_software,
                              appengine_hostname=appengine_hostname)
