FROM gcr.io/google_appengine/python

# Add the appengine compat library.
COPY appengine-compat /opt/appengine-compat

# Add the vmruntime
COPY appengine-vmruntime /opt/appengine-vmruntime

# Create a virtualenv. This virtualenv will contain the compat library,
# vmruntime, and the user's app's dependencies.
RUN virtualenv /env
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

# Install the compat library and the vmruntime.
RUN pip install --upgrade /opt/appengine-compat /opt/appengine-vmruntime

# Install the default WSGI server and dependencies.
COPY resources/requirements.txt /opt/requirements.txt
RUN pip install --upgrade -r /opt/requirements.txt

# Setup the application directory
WORKDIR /app

# Add the default gunicorn configuration file to the app directory. This
# default file will be overridden if the user adds a file called
# "gunicorn.conf.py" to their app's root directory.
ADD resources/gunicorn.conf.py /app/gunicorn.conf.py

# Expose port 8080, the default HTTP traffic port
EXPOSE 8080

# Configure the entrypoint with Managed VMs-essential configuration like "bind",
# but leave the rest up to the config file.
ENTRYPOINT [\
    "/env/bin/gunicorn",\
    "-b", ":8080",\
    "vmruntime.wsgi:meta_app",\
    "--log-file=-",\
    "-c", "gunicorn.conf.py"]
