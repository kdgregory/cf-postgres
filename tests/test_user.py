""" Unit tests for the User sub-resource. These tests verify the behavior of
    the handler, but do not attempt to verify that it executed the correct SQL.
    Some tests mock out the internal action methods to verify that they've been
    called correctly, while others check the overall flow by looking at the
    response object.
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


RESOURCE_TYPE       = "User"
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
def mock_secret(monkeypatch):
    secret_value= {
                  'username': USERNAME,
                  'password': PASSWORD,
                  }
    mock = Mock(return_value=secret_value)
    monkeypatch.setattr(util, 'retrieve_json_secret', mock)
    return mock


@pytest.fixture
def no_secret(monkeypatch):
    # for tests that shouldn't retrieve a secret, this will throw
    monkeypatch.setattr(util, 'retrieve_json_secret', Mock(side_effect = Exception("should not be called")))


@pytest.fixture
def mock_create(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(user_handler, 'doCreate', mock)
    return mock


@pytest.fixture
def mock_update(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(user_handler, 'doUpdate', mock)
    return mock


@pytest.fixture
def mock_delete(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(user_handler, 'doDelete', mock)
    return mock


################################################################################
## testcases
################################################################################

# this tests the end-to-end flow, mocking only the connection
def test_create_flow(no_secret, mock_connection, response_holder):
    props = {
                "Username": USERNAME,
                "Password": PASSWORD,
            }
    assert user_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, props, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": USERNAME,
                              }


def test_create_flow_missing_props(no_secret, mock_connection, response_holder):
    props = { }
    assert user_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, props, response_holder)
    assert response_holder == {
                              "Status": "FAILED",
                              "Reason": "Must specify username or secret",
                              "PhysicalResourceId": "unknown",
                              }
    
    
def test_create_from_props(no_secret, mock_connection, response_holder, mock_create):
    props = {
                "Username":       USERNAME,
                "Password":       PASSWORD,
                "CreateDatabase": "true",
                "CreateRole":     "TRUE",
            }
    assert user_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, props, response_holder)
    mock_create.assert_called_once_with(mock_connection, USERNAME, PASSWORD, True, True, response_holder)


def test_create_from_secret(mock_secret, mock_connection, response_holder, mock_create):
    props = {
                "UserSecretArn": SECRET_ARN,
            }
    assert user_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, props, response_holder)
    mock_secret.assert_called_once_with(SECRET_ARN)
    mock_create.assert_called_once_with(mock_connection, USERNAME, PASSWORD, False, False, response_holder)


def test_update_flow(no_secret, mock_connection, response_holder):
    props = {
                "Username":     USERNAME,
            }
    assert user_handler.try_handle(mock_connection, "Update", RESOURCE_TYPE, USERNAME, props, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": USERNAME,
                              }
    
def test_update_flow_missing_props(no_secret, mock_connection, response_holder):
    props = {}
    assert user_handler.try_handle(mock_connection, "Update", RESOURCE_TYPE, USERNAME, props, response_holder)
    assert response_holder == {
                              "Status": "FAILED",
                              "Reason": "Must specify username or secret",
                              "PhysicalResourceId": "unknown",
                              }
    
    
def test_update_flow_different_username(no_secret, mock_connection, response_holder):
    props = {
                "Username": "something_else",
            }
    assert user_handler.try_handle(mock_connection, "Update", RESOURCE_TYPE, USERNAME, props, response_holder)
    assert response_holder == {
                              "Status": "FAILED",
                              "Reason": "Can not update username",
                              "PhysicalResourceId": USERNAME,
                              }


def test_update_from_props(mock_secret, mock_connection, response_holder, mock_update):
    props = {
                "Username":       USERNAME,
                "CreateDatabase": "true",
                "CreateRole":     "TRUE",
            }
    assert user_handler.try_handle(mock_connection, "Update", RESOURCE_TYPE, USERNAME, props, response_holder)
    mock_update.assert_called_once_with(mock_connection, USERNAME, None, True, True, response_holder)


def test_update_from_secret(mock_secret, mock_connection, response_holder, mock_update):
    props = {
                "UserSecretArn":    SECRET_ARN,
            }
    assert user_handler.try_handle(mock_connection, "Update", RESOURCE_TYPE, USERNAME, props, response_holder)
    mock_update.assert_called_once_with(mock_connection, USERNAME, PASSWORD, False, False, response_holder)
    

def test_delete_flow(no_secret, mock_connection, response_holder):
    props = {
                "Username":     USERNAME,
            }
    assert user_handler.try_handle(mock_connection, "Delete", RESOURCE_TYPE, USERNAME, props, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": USERNAME,
                              }


def test_delete_flow_missing_props(no_secret, mock_connection, response_holder):
    props = {}
    assert user_handler.try_handle(mock_connection, "Delete", RESOURCE_TYPE, USERNAME, props, response_holder)
    assert response_holder == {
                              "Status": "FAILED",
                              "Reason": "Must specify username or secret",
                              "PhysicalResourceId": "unknown",
                              }
    
def test_update_ignores_username_property(mock_secret, mock_connection, response_holder, mock_delete):
    props = {
                "Username":       "anything",
            }
    assert user_handler.try_handle(mock_connection, "Delete", RESOURCE_TYPE, USERNAME, props, response_holder)
    mock_delete.assert_called_once_with(mock_connection, USERNAME, response_holder)
