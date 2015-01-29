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
"""Bootstrap script to run an App Engine python app on a VM.

This script determines the path to the yaml file, relative to the app directory,
either from an environment variable, or as a backup, from its sole argument.
This script assumes it is being executed from the base of the app directory.
"""







from google.appengine.ext.vmruntime import initialize
initialize.InitializeThreadingApis()
initialize.InitializeFileLogging()
initialize.InitializeApiLogging()

import logging
import os
import sys
import time

from google.appengine.ext.vmruntime import vmservice


logging.basicConfig(level=logging.INFO)


def main():
  if 'MODULE_YAML_PATH' in os.environ:
    module_yaml_path = os.environ['MODULE_YAML_PATH']
    logging.info('Using module_yaml_path from env: %s', module_yaml_path)
  else:
    assert len(sys.argv) == 2, 'Invalid usage. See docstring.'
    module_yaml_path = sys.argv[1]
    logging.info('Using module_yaml_path from argv: %s', module_yaml_path)


  sys.path.insert(0, os.getcwd())

  os.environ['TZ'] = 'UTC'
  time.tzset()

  vmservice.CreateAndRunService(module_yaml_path)


if __name__ == '__main__':
  main()
