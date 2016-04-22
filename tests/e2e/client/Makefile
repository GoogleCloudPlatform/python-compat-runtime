include ../../../common.mk

.PHONY: all
all: upload test

.PHONY: test
test:
	virtualenv env
	env/bin/pip install -r requirements.txt
	env/bin/python main.py http://${GCLOUD_PROJECT}.appspot.com/

.PHONY: upload
upload:
	-e gsutil mb ${BUCKET} &> /dev/null
	gsutil rm ${BUCKET}/**
	gsutil cp ../tests/* ${BUCKET} &> /dev/null
