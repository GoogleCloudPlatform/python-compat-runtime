import multiprocessing

# Use the default worker + threads. Thread-based concurrency is provided via
# the 'futures' package. 'gevent' or other workers would be candidates, except
# that the ndb library has its own concurrency model that conflicts with gevent
# and possibly similar approaches.
worker_class = 'sync'

# Use a number of workers equal to the number of CPU cores available.
# Reducing this number on a multicore instance will reduce memory consumption,
# but will also reduce the app's ability to utilize all available CPU resources.
workers = multiprocessing.cpu_count()

# Use an arbitrary number of threads for concurrency. This will dictate the
# maximum number of requests handled concurrently by EACH worker. Consider
# increasing this number for applications that spend a lot of time waiting for
# I/O.
threads = 100

# Settings specific to the Managed VMs production environment such as "bind"
# and "logfile" are set in the Dockerfile's ENTRYPOINT directive.
