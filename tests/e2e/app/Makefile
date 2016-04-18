include ../../../common.mk

.PHONY: all
all: deploy

.PHONY: deploy
deploy: build-base generate-dockerfile copy-tests
	gcloud preview app deploy -q

.PHONY: build-base
build-base:
	$(MAKE) -C ../../.. push

.PHONY: generate-dockerfile
generate-dockerfile:
	sed "s#\$$DOCKER_IMAGE_NAME#$(DOCKER_IMAGE_NAME)#g" Dockerfile.in > Dockerfile

.PHONY: copy-tests
copy-tests:
	cp -r ../tests .
