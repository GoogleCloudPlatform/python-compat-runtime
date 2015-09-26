Google Managed VMs Python Runtime
=================================

Warning
-------
The instructions here are for a multi-process version of the Python 2.7 runtime
**currently in beta**. To use the stable version of the runtime, follow the
documentation at https://cloud.google.com/appengine/docs/managed-vms/ instead.

Contents
--------
   * Using the multi-process runtime
   * Configuration
   * Building your own version
   * Caveats

Using the multi-process runtime
-------------------------------
*These instructions assume you have a working Python application that has
already been deployed successfully to Managed VMs using the default runtime
version.*

As this version of the Python runtime is currently in beta, it is not built
as a stable Docker image like other runtimes. Instead it can be put into place
via modifications to an application's Dockerfile.

If your application has an automatically generated Dockerfile (this will be
created during the deployment process the first time your app is deployed),
copy multicore_runtime/dev/Dockerfile from this repository to your application
directory.

If your application has a custom Dockerfile, then compare the two files and
merge them. In typical cases this can be done by removing the first line of your
application's Dockerfile (starting with FROM) and the last line of
multicore_runtime/dev/Dockerfile (ADD . /app) and concatenating the files, with
the repository's version first.

Also copy the gunicorn_config.py file from the repository to your application's
root directory. (When the runtime is prepared as a precompiled image, a default
will be included in the image and this step will become optional.)

This Dockerfile will download the latest release of the runtime directly from
Github. If you would like to instead use a version of the runtime you have
modified or that has not yet been released, see the "Building your own version"
section.

*Post-release, this version of the Python runtime will be made available as a
prebuilt Docker image with no manual Dockerfile modification required.*

Configuration
-------------
By default the multi-process version of the runtime is launched via the Gunicorn
webserver and is configured to use gevent-based concurrency and a number of
processes equal to the number of CPU cores available.

This can be changed by creating a file called "gunicorn_config.py" in your
application's root directory, which will override the default
"gunicorn_config.py" included with this project. Refer the gunicorn
documentation for details:
http://gunicorn-docs.readthedocs.org/en/latest/settings.html

Building your own version
-------------------------
If you would like to make modifications to the runtime (either for personal use
or to debug or resolve an outstanding issue), you can build and deploy a custom
version with the following steps:

- After cloning the repository locally and making your changes, build a source
distribution by running `python setup.py sdist` from the root directory of the
repository.
- Copy the resulting tar.gz file to your application's folder, in the same
directory as the Dockerfile.
- Also copy "gunicorn_config.py" to the same directory as above, or use your
own.
- Edit the Dockerfile in your application and look for the line that says
`ADD (...) /home/vmagent/python-runtime.tar.gz`
- Replace that line with a COPY command, with the filename of your generated
tar.gz file instead of the URL as the source, and the same destination. An
example is included in the Dockerfile comments.
- Deploy your application. A warning during deployment where your tar.gz file is
rejected for addition because it is too large can be ignored.

Caveats
-------
As this is a beta product, some functionality has not yet been implemented.

- Handlers that are flagged as `login: required` or `login: admin` are not
supported. Attemping to access these handlers will result in a 404 as the
handlers will not be registered.

There may be other features that work on the current Python runtime and are not
implemented or not functional in this version. Please open an issue on Github
for any you encounter.
