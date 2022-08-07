.PHONY: default deploy package test quicktest init clean

LAMBDA_NAME     ?= cf_postgres

POETRY_DIST_DIR := $(PWD)/dist
BUILD_DIR       := $(PWD)/build
DEPLOY_DIR      := $(PWD)
ARTIFACT        := lambda.zip

default: package

deploy: package
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(DEPLOY_DIR)/$(ARTIFACT)

package: test
	poetry build
	mkdir -p $(BUILD_DIR)
	poetry run pip install --upgrade -t $(BUILD_DIR) $(POETRY_DIST_DIR)/*.whl
	cd $(BUILD_DIR) ; zip -r $(DEPLOY_DIR)/$(ARTIFACT) . -x '*.pyc'

test:	init quicktest

quicktest:
	# poetry run pytest
	echo "no tests yet"

init:
	poetry install

clean:
	rm -rf $(POETRY_DIST_DIR)
	rm -rf $(BUILD_DIR)
	rm $(DEPLOY_DIR)/$(ARTIFACT)
	rm -rf */__pycache__