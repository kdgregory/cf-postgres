""" Unit tests for the CreateUser action. These tests verify the behavior of the handler,
    but do not attempt to verify that it executed the correct SQL.
    """

import copy
import json
import pytest
from unittest.mock import Mock, patch, ANY

from cf_postgres import util
from cf_postgres.handlers import user_handler


################################################################################
# event properties that will be asserted
################################################################################


RESOURCE            = "User"
USERNAME            = "tester"
PASSWORD            = "tester-123"
ADMIN_SECRET_ARN    = "arn:aws:secretsmanager:us-east-1:123456789012:secret:database-1-admin-5z4FyE"
SECRET_ARN          = "arn:aws:secretsmanager:us-east-1:123456789012:secret:database-1-user-9qqMq4"


################################################################################
## fixtures
################################################################################


@pytest.fixture
def mock_connection():
    return Mock()


@pytest.fixture
def response_holder():
    return {}


@pytest.fixture
def with_secret(monkeypatch):
    secret_value= {
                  'username': USERNAME,
                  'password': PASSWORD,
                  }
    monkeypatch.setattr(util, 'retrieve_json_secret', Mock(return_value=secret_value))


@pytest.fixture
def no_secret(monkeypatch):
    # for tests that shouldn't retrieve a secret, this will throw
    monkeypatch.setattr(util, 'retrieve_json_secret', Mock(side_effect = Exception("should not be called")))


################################################################################
## testcases
################################################################################


def test_create_from_username(no_secret, mock_connection, response_holder):
    props = {
                "Username":     USERNAME,
                "Password":     PASSWORD
            }
    assert user_handler.try_handle(RESOURCE, "Create", mock_connection, props, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": USERNAME,
                              }


def test_create_from_secret(with_secret, mock_connection, response_holder):
    props = {
                "SecretArn":    SECRET_ARN,
            }
    assert user_handler.try_handle(RESOURCE, "Create", mock_connection, props, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": USERNAME,
                              }


def test_create_missing_props(no_secret, mock_connection, response_holder):
    props = { }
    assert user_handler.try_handle(RESOURCE, "Create", mock_connection, props, response_holder)
    assert response_holder == {
                              "Status": "FAILED",
                              "Reason": "Must specify username or secret",
                              "PhysicalResourceId": "unknown",
                              }


def test_update(no_secret, mock_connection, response_holder):
    props = {
                "Username":     USERNAME,
            }
    assert user_handler.try_handle(RESOURCE, "Update", mock_connection, props, response_holder)
    assert response_holder == {
                              "Status": "FAILED",
                              "Reason": "Can not update a user once created",
                              "PhysicalResourceId": USERNAME,
                              }

def test_delete_from_username(no_secret, mock_connection, response_holder):
    props = {
                "Username":     USERNAME,
            }
    assert user_handler.try_handle(RESOURCE, "Delete", mock_connection, props, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": USERNAME,
                              }


def test_create_from_secret(with_secret, mock_connection, response_holder):
    props = {
                "UserSecretArn":    SECRET_ARN,
            }
    assert user_handler.try_handle(RESOURCE, "Delete", mock_connection, props, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": USERNAME,
                              }


def test_delete_missing_props(no_secret, mock_connection, response_holder):
    props = {}
    assert user_handler.try_handle(RESOURCE, "Delete", mock_connection, props, response_holder)
    assert response_holder == {
                              "Status": "FAILED",
                              "Reason": "Must specify username or secret",
                              "PhysicalResourceId": "unknown",
                              }
