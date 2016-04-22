include ../../../common.mk

.PHONY: all
all: lint upload test

.PHONY: test
test: virtualenv
	virtualenv env
	env/bin/python main.py http://${GCLOUD_PROJECT}.appspot.com/

.PHONY: upload
upload:
	-e gsutil mb ${BUCKET} &> /dev/null
	gsutil rm ${BUCKET}/**
	gsutil cp ../tests/* ${BUCKET} &> /dev/null

.PHONY: virtualenv
virtualenv:
	virtualenv env
	env/bin/pip install -r requirements.txt

.PHONY: lint
lint: virtualenv
	env/bin/flake8 --import-order-style=google ../tests
