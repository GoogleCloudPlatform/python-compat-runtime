include common.mk

.PHONY: build
build:
	docker build --no-cache=$(FORCE_REBUILD) --pull=$(FORCE_REBUILD) \
		-t $(DOCKER_IMAGE_NAME) .

.PHONY: push
push: build
	gcloud docker push $(DOCKER_IMAGE_NAME)

.PHONY: test-vmruntime
test-vmruntime:
	cd appengine-vmruntime && tox

.PHONY: test-e2e
test-e2e:
	$(MAKE) -C tests/e2e all

.PHONY: test
test: test-vmruntime test-e2e
