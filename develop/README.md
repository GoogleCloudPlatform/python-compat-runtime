# Development App

This is a barebones app to use when developing changes to the core runtime components, such as the base docker image and vmruntime library.

This works by:

1. Building a custom version of the base image and pushing it to gcr.io.
2. Building the app's image using the custom base image.

This allows you to replicate the end-to-end image building process while developing. The end-to-end test app uses the same build method.

## Usage

Just use `make all`.
