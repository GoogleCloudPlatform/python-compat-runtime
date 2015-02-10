import logging
import re

from werkzeug.wrappers import Request

def dispatcher(handlers):
  """Accepts handlers and returns a WSGI app that dispatches requests to them.
  
  The list of handlers is as produced by wsgi.load_user_scripts_into_handlers:
  a list of tuples of (url, script, app).
  """

  def dispatch(env, start_response):
    """Handle one request."""
    request = Request(env)
    for url, script, app in handlers: # Closure over parent func's handlers.
      matcher = re.match(url, request.path)
      if matcher and matcher.end() == len(request.path):
        if script:
          if app is not None:
            # Send a response via the app specified in the handler.
            return app(env, start_response)
          else:
            # The import must have failed. This will have been logged at import
            # time. Send a 500 error response.
            start_response('500 Internal Server Error', [])
            return ['<h1>500 Internal Server Error</h1>\n']
        # This is a static file; normally these are handled by the appserver
        # but in development or for local queries they may end up here.
        # TODO: support static files.
        else:
            logging.error('Static file serving is not supported: %s ',
                          request.path)
            start_response('500 Internal Server Error', [])
            return ['<h1>500 Internal Server Error</h1>\n']
    logging.error('No handler found for %s', request.path)
    start_response('404 Not Found', [])
    return ['<h1>404 Not Found</h1>\n']

  return dispatch
