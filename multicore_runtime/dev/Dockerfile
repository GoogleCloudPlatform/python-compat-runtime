# Base Dockerfile for all AppEngine runtime implementations.
FROM google/debian:wheezy
# Clean any CMD that might be inherited from previous image, because that
# will pollute our ENTRYPOINT, see
# http://docs.docker.io/en/latest/reference/builder/#entrypoint.
CMD []
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get -q update && \
  apt-get install --no-install-recommends -y -q ca-certificates net-tools lsof \
    python2.7 python-pip python-gevent python-greenlet && \
  apt-get -y -q upgrade && apt-get clean && rm /var/lib/apt/lists/*_*

ADD python_vm_runtime.tar.gz /home/vmagent/python_vm_runtime

EXPOSE 8080

RUN ln -s /home/vmagent/app /app
WORKDIR /app

RUN ln -s /home/vmagent/python_vm_runtime/google /home/vmagent/app/google

ENTRYPOINT ["/usr/bin/env", "gunicorn", "-w", "4", "-k", "gevent", "-b", "0.0.0.0:8080", "wsgi:meta_app", "--log-file=-"]

ADD . /home/vmagent/app/

RUN pip install -r base_requirements.txt
