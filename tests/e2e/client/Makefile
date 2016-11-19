include ../../../common.mk

.PHONY: all
all: lint upload test

.PHONY: test
test: virtualenv
	virtualenv env
	env/bin/python main.py http://${GCLOUD_PROJECT}.appspot.com/

.PHONY: upload
upload:
	-gsutil mb ${BUCKET}
	-gsutil -m rm ${BUCKET}/**
	gsutil -m cp ../tests/* ${BUCKET}

.PHONY: virtualenv
virtualenv:
	virtualenv env
	env/bin/pip install -r requirements.txt

.PHONY: lint
lint: virtualenv
	env/bin/flake8 --import-order-style=google ../tests
