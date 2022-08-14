.PHONY: default deploy package itest test quicktest init clean

LAMBDA_NAME     ?= cf_postgres

SRC_DIR         := $(PWD)/src
BUILD_DIR       := $(PWD)/build
LIB_DIR         := $(BUILD_DIR)/lib
ARTIFACT        := lambda.zip

PG_PASSWORD	?= "postgres"
PG_PORT		?= 9432

default: package

deploy: package
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(BUILD_DIR)/$(ARTIFACT)

package: test
	cd $(SRC_DIR) ; zip -q -r $(BUILD_DIR)/$(ARTIFACT) . -x '*.pyc'
	cd $(LIB_DIR) ; zip -q -r $(BUILD_DIR)/$(ARTIFACT) . -x '*.pyc'

itest:	test
	CONTAINER_ID=$$(docker run -d --rm -e POSTGRES_PASSWORD=$(PG_PASSWORD) -p $(PG_PORT):5432 postgres:12) && \
	PYTHONPATH=$(LIB_DIR):$(SRC_DIR) PGPORT=$(PG_PORT) PGPASSWORD=$(PG_PASSWORD) python -m unittest itests/test*.py ; \
	docker kill $${CONTAINER_ID}

test:	$(LIB_DIR) quicktest

quicktest:
	PYTHONPATH=$(LIB_DIR):$(SRC_DIR) python -m unittest tests/test*.py


$(LIB_DIR): requirements.txt
	mkdir -p $(LIB_DIR)
	touch $(LIB_DIR)
	pip install -U -r requirements.txt -t $(LIB_DIR)

clean:
	rm -rf $(BUILD_DIR)
	rm -rf */__pycache__
