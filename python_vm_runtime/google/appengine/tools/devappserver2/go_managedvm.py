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
"""An abstraction around the source and executable for a Go Managed VM app."""

import atexit
import logging
import os
import os.path
import shutil
import subprocess
import sys
import tempfile

import google
from google.appengine.tools.devappserver2 import go_errors
from google.appengine.tools.devappserver2 import safe_subprocess


def _rmtree(directory):
  try:
    shutil.rmtree(directory)
  except OSError:
    pass


def _run_tool(tool, extra_args):
  """Run external executable tool.

  Args:
    tool: string name of the tool to run.
    extra_args: additional arguments for tool.

  Returns:
    A tuple of the (stdout, stderr) from the process.

  Raises:
    BuildError: if tool fails.
  """
  args = [tool]
  if sys.platform.startswith('win'):
    args = [tool + '.exe']
  args.extend(extra_args)
  logging.debug('Calling: %s', ' '.join(args))
  try:
    process = safe_subprocess.start_process(args,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
  except OSError as e:
    msg = '%s not found.' % args[0]
    raise go_errors.BuildError('%s\n%s' % (msg, e))
  if process.returncode:
    raise go_errors.BuildError(
        '(Executed command: %s)\n\n%s\n%s' % (' '.join(args), stdout, stderr))
  return stdout, stderr


class GoManagedVMApp(object):
  """An abstraction around the source and executable for a Go Managed VM app."""

  def __init__(self, module_configuration):
    """Initializer for Module.

    Args:
      module_configuration: An application_configuration.ModuleConfiguration
          instance storing the configuration data for a module.
    """
    self._module_configuration = module_configuration
    self._go_executable = None
    self._work_dir = None

  @property
  def go_executable(self):
    """The path to the Go executable. None if it has not been built."""
    return self._go_executable

  def get_environment(self):
    """Return the environment that will be used to run the Go executable."""
    environ = {'RUN_WITH_DEVAPPSERVER': '1'}
    if 'SYSTEMROOT' in os.environ:
      environ['SYSTEMROOT'] = os.environ['SYSTEMROOT']
    if 'USER' in os.environ:
      environ['USER'] = os.environ['USER']
    return environ

  def _build(self):
    """Builds the Managed VM app locally.

    Note that the go compiler must be called from within the app directory.
    Otherwise, it returns an error like:
    can't load package: package /a/b: import "/a/b": cannot import absolute path

    Raises:
      BuildError: if build fails.
    """
    logging.debug('Building Go application')

    app_root = self._module_configuration.application_root
    exe_name = os.path.join(self._work_dir, '_ah_exe')
    args = ['build', '-tags', 'appenginevm', '-o', exe_name]
    try:
      cwd = os.getcwd()
      os.chdir(app_root)
      stdout, stderr = _run_tool('go', args)
    finally:
      os.chdir(cwd)
    logging.debug('Build succeeded:\n%s\n%s', stdout, stderr)
    self._go_executable = exe_name

  def maybe_build(self, maybe_modified_since_last_build):
    """Builds an executable for the application if necessary.

    Args:
      maybe_modified_since_last_build: True if any files in the application root
          or the GOPATH have changed since the last call to maybe_build, False
          otherwise. This argument is used to decide whether a build is Required
          or not.

    Returns:
      True if compilation was successfully performed (will raise
        an exception if compilation was attempted but failed).
      False if compilation was not attempted.

    Raises:
      BuildError: if building the executable fails for any reason.
    """
    if not self._work_dir:
      self._work_dir = tempfile.mkdtemp('appengine-go-bin')
      atexit.register(_rmtree, self._work_dir)

    if self._go_executable and not maybe_modified_since_last_build:
      return False

    if self._go_executable:
      logging.debug('Rebuilding Go application due to source modification')
    else:
      logging.debug('Building Go application')
    self._build()
    return True
