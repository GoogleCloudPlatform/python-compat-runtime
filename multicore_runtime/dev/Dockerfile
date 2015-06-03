FROM gcr.io/google_appengine/base

RUN apt-get -q update && \
  apt-get install --no-install-recommends -y -q \
    python2.7 python-pip python-gevent python-greenlet && \
  apt-get clean && rm /var/lib/apt/lists/*_*

COPY appengine-python-vm-runtime-0.1.tar.gz /home/vmagent/python-runtime.tar.gz

RUN pip install --upgrade pip>=6.1.1 gunicorn==19.1.1
RUN pip install /home/vmagent/python-runtime.tar.gz

EXPOSE 8080

RUN ln -s /home/vmagent/app /app
WORKDIR /app

ENTRYPOINT ["/usr/bin/env", "gunicorn", "-w", "4", "-k", "gevent", "-b", "0.0.0.0:8080", "google.appengine.vmruntime.wsgi:meta_app", "--log-file=-"]

ADD . /app
