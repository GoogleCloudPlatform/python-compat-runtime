import multiprocessing

# Set the worker class to 'gevent'. Gevent provides green thread-based
# concurrency and non-blocking I/O by monkey-patching I/O features in the
# standard library. This can be changed to 'sync' to remove green thread
# concurrency entirely, but this will impact performance under load.
worker_class = 'gevent'

# Set the number of workers to equal the number of available cores. This should
# be increased to e.g. 2x or 3x the number of available cores, up to limits of
# available memory, if the worker_class is set to 'sync'.
workers = multiprocessing.cpu_count()

# Settings specific to the Managed VMs production environment such as "bind"
# and "logfile" are set in the Dockerfile's ENTRYPOINT directive.
