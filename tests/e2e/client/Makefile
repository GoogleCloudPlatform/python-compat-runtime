include ../../../common.mk

.PHONY: all
all:
	virtualenv env
	env/bin/pip install -r requirements.txt
	env/bin/python main.py https://${GCLOUD_PROJECT}.appspot.com/
