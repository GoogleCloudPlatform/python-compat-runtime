FROM gcr.io/google_appengine/python

# Add the appengine compat library.
COPY appengine-compat /opt/appengine-compat

# Add the vmruntime
COPY appengine-vmruntime /opt/appengine-vmruntime

# Install the compat library and the vmruntime.
RUN easy_install pip
RUN pip install --upgrade /opt/appengine-compat /opt/appengine-vmruntime

# Install requirements needed by the default configuration.
COPY resources/requirements.txt /opt/requirements.txt
RUN pip install --upgrade -r /opt/requirements.txt

# Setup the application directory
RUN ln -s /home/vmagent/app /app
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
    "/usr/bin/env",\
    "gunicorn", "-b", ":8080",\
    "vmruntime.wsgi:meta_app",\
    "--log-file=-",\
    "-c", "gunicorn.conf.py"]
