GCLOUD_PROJECT:=$(shell gcloud config list project --format="value(core.project)")

.PHONY: deploy
deploy: build-base generate-dockerfile
	gcloud preview app deploy -q

.PHONY: build-base
build-base:
	docker build -t gcr.io/$(GCLOUD_PROJECT)/google-python-compat ../..
	gcloud docker push gcr.io/$(GCLOUD_PROJECT)/google-python-compat

.PHONY: generate-dockerfile
generate-dockerfile:
	sed "s/\$$GCLOUD_PROJECT/$(GCLOUD_PROJECT)/g" Dockerfile.in > Dockerfile

.PHONY: test
test:
	curl https://$GCLOUD_PROJECT.appspot.com
