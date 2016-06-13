# Unless manually set, this determines the tag name for the docker image
# based on the current gcloud project name.
ifeq ($(origin DOCKER_IMAGE_NAME), undefined)
	GCLOUD_PROJECT:=$(shell gcloud config list project --format="value(core.project)")
	DOCKER_IMAGE_NAME:=gcr.io/$(GCLOUD_PROJECT)/google-python-compat
endif
ifeq ($(origin FORCE_REBUILD), undefined)
	FORCE_REBUILD:=false
endif
BUCKET=gs://${GCLOUD_PROJECT}-python-compat-e2e-tests
