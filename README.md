Google App Engine Managed VMs Python Compat Runtime
===================================================

Warning
-------
The instructions here are for a multi-process version of the Python 2.7 runtime
**currently in alpha**. To use the stable version of the runtime, follow the
documentation at https://cloud.google.com/appengine/docs/managed-vms/ instead.

Using this runtime
------------------

Please refer to [the docs](https://cloud.google.com/appengine/docs/managed-vms/python/migrating-an-existing-app) on how to use and customize this runtime.

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
As this is a alpha product, some functionality has not yet been implemented.

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
