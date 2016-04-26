Google App Engine Flexible Environment Python Compat Runtime
===================================================

This repository contains the source code used for the [App Engine Flexible Environment](https://cloud.google.com/appengine/docs/flexible/) Python Compat runtime.  This runtime provides best effort compatibility with applications written to target the App Engine Standard Environment with Python 2.7. This runtime is currently in *alpha*.

This runtime is intended for users migrating applications from App Engine Standard to App Engine Flex. For users building new applications on App Engine with Python, we recommend following the [getting started guide](https://cloud.google.com/python).  


Using this runtime
------------------
Please refer to [the docs](https://cloud.google.com/appengine/docs/flexible/python/migrating-an-existing-app) on how to use and customize this runtime.

Gunicorn configuration
----------------------
By default the multi-process version of the runtime is launched via the Gunicorn
webserver and is configured to use gevent-based concurrency and a number of
processes equal to the number of CPU cores available.

This can be changed by creating a file called `gunicorn.conf.py` in your
application's root directory, which will override the default
`gunicorn.conf.py` included with this project. Refer the [gunicorn documentation](http://gunicorn-docs.readthedocs.org/en/latest/settings.html) for details.

Caveats
-------
This runtime is currently an alpha.  As this is a alpha product, some functionality has not yet been implemented, and a few things may change.  

Notably:
* Handlers in `app.yaml `that are flagged as `login: required` or `login: admin` are not supported. Attemping to access these handlers will result in a 404 as the handlers will not be registered.
* `threadsafe: false` in `app.yaml` is ignored. Your application must either be threadsafe or you much change the gunicorn configuration to use sync workers.

There may be other features that work on the current Python runtime and are not
implemented or not functional in this version. Please open an issue on Github
for any you encounter.

Contributing changes
--------------------

See [CONTRIBUTING.md](CONTRIBUTING.md)

Licensing
---------

See [LICENSE](LICENSE)
