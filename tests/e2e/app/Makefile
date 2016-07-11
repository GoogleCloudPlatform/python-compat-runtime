include ../../../common.mk

.PHONY: all
all: deploy

.PHONY: deploy
deploy: build-base generate-dockerfile generate-app-yaml
	gcloud app deploy -q

.PHONY: build-base
build-base:
	$(MAKE) -C ../../.. push

.PHONY: generate-dockerfile
generate-dockerfile:
	sed "s#\$$DOCKER_IMAGE_NAME#$(DOCKER_IMAGE_NAME)#g" Dockerfile.in > Dockerfile

.PHONY: generate-app-yaml
generate-app-yaml:
	sed "s#\$$CLOUD_STORAGE_BUCKET#$(BUCKET)#g" app.yaml.in > app.yaml
