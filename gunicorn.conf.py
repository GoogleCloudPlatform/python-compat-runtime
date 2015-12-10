import multiprocessing

# Use threaded workers. Thread-based concurrency is provided via the 'futures'
# package. 'gevent' or other workers would be candidates, except that the ndb
# library has its own concurrency model that conflicts with gevent and possibly
# with similar approaches.
worker_class = 'gthread'

# Use a number of workers equal to the number of CPU cores available.
# Reducing this number on a multicore instance will reduce memory consumption,
# but will also reduce the app's ability to utilize all available CPU resources.
workers = multiprocessing.cpu_count()

# Use an arbitrary number of threads for concurrency. This will dictate the
# maximum number of requests handled concurrently by EACH worker.
threads = 25

# Settings specific to the Managed VMs production environment such as "bind"
# and "logfile" are set in the Dockerfile's ENTRYPOINT directive.
