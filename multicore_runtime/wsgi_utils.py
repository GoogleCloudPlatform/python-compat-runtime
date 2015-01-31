import logging
import os

from google.appengine.api import appinfo_includes
from google.appengine.runtime import wsgi


def get_module_config_filename():
  """Returns the name of the module configuration file (app.yaml)."""
  module_yaml_path = os.environ['MODULE_YAML_PATH']
  logging.info('Using module_yaml_path from env: %s', module_yaml_path)
  return module_yaml_path

def get_module_config(filename):
  with open(filename) as f:
    return appinfo_includes.Parse(f)

def normalize_script(script):
  """Translates $PYTHON_LIB in the given script. Returns the translation."""
  if script:
    return script.replace('$PYTHON_LIB/', '')
  return script

def app_for_script(script):
  if script:
    app, filename, err = wsgi.LoadObject(script)
    if err:
      # Log the exception but do not reraise.
      logging.exception('Failed to import %s: %s', script, err)
      return None
    else:
      return app

def load_user_scripts_into_handlers(handlers):
  """Accepts appinfo_external.handlers data and returns preloaded user scripts.

  Returns a list of tuples suitable for configuring the dispatcher() app,
  where the tuples are (url, script, app):
    - url: The url pattern which matches this handler.
    - script: The script to serve for this handler, as a string.
    - app: The fully loaded app corresponding to the script.
  """

  loaded_handlers = [(x.url,
                     normalize_script(x.script),
                     app_for_script(x.script) if x.script else None)
                     for x in handlers]
  logging.info('Parsed handlers: %s', [(x[0], x[1]) for x in loaded_handlers])
  return loaded_handlers
