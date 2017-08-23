DEPRECATED: Google App Engine Flexible Environment Python Compat Runtime
===================================================

This repository contains the source code used for the [App Engine Flexible Environment](https://cloud.google.com/appengine/docs/flexible/) Python Compat (multicore) runtime, corresponding to `env:flex` + `runtime: python-compat` in your `app.yaml`.  This runtime provides best effort compatibility with applications written to target the App Engine Standard Environment with Python 2.7. This runtime is [**deprecated**](https://cloud.google.com/appengine/docs/flexible/python/upgrading#runtime_deprecations) and incomplete.


Using this runtime
------------------
**Do not use this runtime for new development**.  If you are using this runtime, you should expediently migrate to the [vanilla Python runtime](https://cloud.google.com/appengine/docs/flexible/python/migrating) before **November 2017**.

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
This runtime is deprecated and incomplete.  Only critical bug fixes are planned.

Notably:
* Handlers in `app.yaml `that are flagged as `login: required` or `login: admin` are not supported. Attemping to access these handlers will result in a 404 as the handlers will not be registered.
* `threadsafe: false` in `app.yaml` is ignored. Your application must either be threadsafe or you much change the gunicorn configuration to use sync workers.
* Deferred TaskQueues are not functional.

There may be other features that are not implemented or not functional in this version.

Contributing changes
--------------------

See [CONTRIBUTING.md](CONTRIBUTING.md)

Licensing
---------

See [LICENSE](LICENSE)
