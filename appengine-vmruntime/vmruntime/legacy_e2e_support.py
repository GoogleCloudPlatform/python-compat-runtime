# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Utilities to support end-to-end tests written for the Python 2.5 runtime."""

import logging
import runpy
import threading
from wsgiref import handlers

from . import wsgi_config

from google.appengine.ext.webapp import util as webapp_util


class MockedWsgiHandler(object):
  """Mock for wsgiref.handler classes."""

  python_25_app_lock = threading.Lock()  # For grabbing the user's python25 app.

  def __init__(self, app_holder):
    self._app_holder = app_holder

  def run(self, app):
    self._app_holder.append(app)


class StubOut(object):
  """Object for setting and then easily removing stubs."""

  def __init__(self):
    # Map from (object, field_str) to pre-stubbed field.
    self._stubs = {}

  def set(self, obj, attr_string, new_attr):
    old_attr = getattr(obj, attr_string)
    self._stubs.setdefault((obj, attr_string), old_attr)
    setattr(obj, attr_string, new_attr)

  def clean_up(self):
    for (obj, field_str), old_value in self._stubs.iteritems():
      setattr(obj, field_str, old_value)


def load_legacy_scripts_into_handlers(handlers):
  """Preloads legacy CGI scripts. Static file handlers are not supported.

  Args:
    handlers: appinfo.handlers data as provided by get_module_config()

  Returns:
    A list of tuples suitable for configuring the dispatcher() app,
    where the tuples are (url, app):
      - url_re: The url regular expression which matches this handler.
      - app: The fully loaded app corresponding to the script.
  """
  loaded_handlers = [
      (x.url,
       legacy_app_for_script(x.script.replace('$PYTHON_LIB/', '')))
      for x in handlers]
  logging.info('Parsed handlers: %r',
               [url_re for (url_re, _) in loaded_handlers])
  return loaded_handlers


def legacy_app_for_script(script):
  """Returns the CGI app specified in the input string, or None on failure.

  Args:
    script: A script specification from a python27 app.yaml. e.g. my.module.app

  Returns:
    The application as extracted from the script, or None.
  """
  with MockedWsgiHandler.python_25_app_lock:
    modname = script.rsplit('.', 1)[0]
    app_holder = []
    revert_func = lambda: None
    try:
      revert_func = stub_wsgi_utils(app_holder)
      runpy.run_module(modname, run_name='__main__')
    except ImportError as e:
      logging.exception('Error loading %s', script)
    finally:
      revert_func()
    if app_holder:
      return app_holder[0]
    else:
      logging.error('Cannot load an app from %s', script)
      return None


# Monkey-patch the python 2.5 CGI/WSGI adapter. In python 2.7, we need to
# execute the user's app for them (in order to add all of the needed
# middleware). In python 2.5, the user executes things themselves. To get
# around this, we'll intercept their execution call.
#
# The intended workflow is:
#   1) User has a script.py as specified as a URL handler in their app.yaml.
#   2) script.py runs the app they care about with util.run_wsgi_app().
#   3) We've actually stubbed that method out so that it just populates
#      a data field that we control.
#   4) We add the appropriate middleware to the app we've intercepted in (3).
def stub_wsgi_utils(output_app_holder):
  """Stub out WSGI adapters for python 2.5-style apps."""
  stubs = StubOut()
  stubbed_wsgi_handler_class = (
      lambda * args, **kwargs: MockedWsgiHandler(output_app_holder))

  def run_wsgi_stub(application):
    output_app_holder.append(application)

  stubs.set(webapp_util, 'run_bare_wsgi_app', run_wsgi_stub)
  stubs.set(webapp_util, 'run_wsgi_app', run_wsgi_stub)
  # In the python2.7 runtime, these handler classes exist. In later python
  # versions, IISCGIHandler is added. But we can't really stub that here since
  # we're running with python2.7.
  stubs.set(handlers, 'BaseHandler', stubbed_wsgi_handler_class)
  stubs.set(handlers, 'SimpleHandler', stubbed_wsgi_handler_class)
  stubs.set(handlers, 'BaseCGIHandler', stubbed_wsgi_handler_class)
  stubs.set(handlers, 'CGIHandler', stubbed_wsgi_handler_class)

  # Return a callable that, when called, undoes the monkey patching.
  return stubs.clean_up
