# Building, Testing, and Deploying

## Pre-requisites

This project use [make](https://www.gnu.org/software/make/) to automate the build and test process.

You will also need:

* [Docker engine](https://www.docker.com/products/docker-engine).
* [Google Cloud SDK](https://cloud.google.com/sdk).
* A Google Cloud project with billing enabled. You will need to run `gcloud init` to setup your project with the SDK.
* [tox](http://tox.readthedocs.org/en/latest/).

## Building

The final product of this repository is a complete runtime docker image.

### Building the runtime

The runtime can be built by running:

    make build

This will build the base image and tag it with `gcr.io/$YOUR_PROJECT_ID/google-python-compat`. This is useful for testing or custom builds of the image. You can push it to `gcr.io` with:

    make push

If you want to push under a different tag, you can set the docker image name before running make:

    export DOCKER_IMAGE_NAME=gcr.io/your-project/python-compat:0.6
    make push

## Testing

### vmruntime tests

This tests the python library located in `appengine-vmruntime`. This is the WSGI app that's used as the entrypoint for user applications.

    make test-vmruntime

### end-to-end tests

There is an application at `tests/e2e-app` that can be used to verify that the new image works as intended. To deploy this application:

    make test-e2e

This will build the base image and then deploy the application. Once it's done deploying, you should be able to access it at `https://your-project-id.appspot.com`. If the page doesn't error, then the runtime is working.

## Developing

When developing, it's best to use the `tests-e2e` app as a guide:

* Build a custom version of the base image.
* Write an app with a custom dockerfile that extends from your custom base image.
* Deploy the app.
