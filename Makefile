.PHONY: default deploy package test quicktest init clean

LAMBDA_NAME     ?= cf_postgres

SRC_DIR         := $(PWD)/src
BUILD_DIR       := $(PWD)/build
LIB_DIR         := $(BUILD_DIR)/lib
ARTIFACT        := lambda.zip

default: package

deploy: package
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(BUILD_DIR)/$(ARTIFACT)

package: test
	cd $(SRC_DIR) ; zip -q -r $(BUILD_DIR)/$(ARTIFACT) . -x '*.pyc'
	cd $(LIB_DIR) ; zip -q -r $(BUILD_DIR)/$(ARTIFACT) . -x '*.pyc'

test:	$(BUILD_DIR) quicktest

quicktest:
	PYTHONPATH=$(LIB_DIR):$(SRC_DIR) python -m unittest tests/*.py


$(BUILD_DIR): requirements.txt
	mkdir -p $(BUILD_DIR)
	pip install -U -r requirements.txt -t $(LIB_DIR)

clean:
	rm -rf $(BUILD_DIR)
	rm -rf */__pycache__
