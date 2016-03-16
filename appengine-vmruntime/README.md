# App Engine Compat VM Runtime

This folder contains the `vmruntime` Python package. This is used to provide an entrypoint to Managed VMs that behaves like Google App Engine Standard. Notably:

* Parses the `app.yaml` (or module-specific yaml) and handles mapping the URLs and WSGI applications defined in the yaml's `handlers` section.
* Handles static files declared in `app.yaml`.
* Sets up Cloud Logging.
* Ensures `google.appengine` API requests are authenticated correctly.
