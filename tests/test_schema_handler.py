""" Unit tests for the Schema sub-resource. These tests verify the behavior of
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
from cf_postgres.handlers import schema_handler


################################################################################
# event properties that will be asserted
################################################################################


RESOURCE_TYPE         = "Schema"
ADMIN_SECRET_ARN      = "arn:aws:secretsmanager:us-east-1:123456789012:secret:database-1-admin-5z4FyE"
SCHEMA_NAME           = "example"
OWNER                 = "me"
USERS                 = ["argle", "bargle"]
RO_USERS              = ["foo", "bar", "baz"]

DEFAULT_PROPS         = {
                        "Name":             SCHEMA_NAME,
                        "Cascade":          "true"
                        }


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
def mock_create(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(schema_handler, 'doCreate', mock)
    return mock


@pytest.fixture
def mock_update(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(schema_handler, 'doUpdate', mock)
    return mock


@pytest.fixture
def mock_delete(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(schema_handler, 'doDelete', mock)
    return mock


################################################################################
## testcases
################################################################################

# this tests the end-to-end flow, mocking only the connection
def test_create_flow(mock_connection, response_holder):
    assert schema_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, DEFAULT_PROPS, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": SCHEMA_NAME,
                              }


def test_create_simple(mock_connection, response_holder, mock_create):
    assert schema_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, DEFAULT_PROPS, response_holder)
    mock_create.assert_called_once_with(mock_connection, SCHEMA_NAME, None, False, False, [], [], response_holder)


def test_create_with_owner(mock_connection, response_holder, mock_create):
    props = copy.deepcopy(DEFAULT_PROPS)
    props['Owner'] = "example"
    assert schema_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, props, response_holder)
    mock_create.assert_called_once_with(mock_connection, SCHEMA_NAME, "example", False, False, [], [], response_holder)


def test_create_with_public_access(mock_connection, response_holder, mock_create):
    props = copy.deepcopy(DEFAULT_PROPS)
    props['Public'] = "true"
    assert schema_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, props, response_holder)
    mock_create.assert_called_once_with(mock_connection, SCHEMA_NAME, None, True, False, [], [], response_holder)


def test_create_with_public_readonly(mock_connection, response_holder, mock_create):
    props = copy.deepcopy(DEFAULT_PROPS)
    props['ReadOnly'] = "true"
    assert schema_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, props, response_holder)
    mock_create.assert_called_once_with(mock_connection, SCHEMA_NAME, None, False, True, [], [], response_holder)


def test_create_with_explicit_users(mock_connection, response_holder, mock_create):
    props = copy.deepcopy(DEFAULT_PROPS)
    props['Users'] = ["foo", "bar", "baz"]
    assert schema_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, props, response_holder)
    mock_create.assert_called_once_with(mock_connection, SCHEMA_NAME, None, False, False, ["foo", "bar", "baz"], [], response_holder)


def test_create_with_readonly_users(mock_connection, response_holder, mock_create):
    props = copy.deepcopy(DEFAULT_PROPS)
    props['ReadOnlyUsers'] = ["argle", "bargle"]
    assert schema_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, props, response_holder)
    mock_create.assert_called_once_with(mock_connection, SCHEMA_NAME, None, False, False, [], ["argle", "bargle"], response_holder)


def test_create_with_all_acls_set(mock_connection, response_holder, mock_create):
    # the implementation will figure this out
    props = copy.deepcopy(DEFAULT_PROPS)
    props['Public'] = "true"
    props['ReadOnly'] = "true"
    props['Users'] = ["foo", "bar", "baz"]
    props['ReadOnlyUsers'] = ["argle", "bargle"]
    assert schema_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, props, response_holder)
    mock_create.assert_called_once_with(mock_connection, SCHEMA_NAME, None, True, True, ["foo", "bar", "baz"], ["argle", "bargle"], response_holder)


def test_update_flow(mock_connection, response_holder):
    assert schema_handler.try_handle(mock_connection, "Update", RESOURCE_TYPE, SCHEMA_NAME, DEFAULT_PROPS, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": SCHEMA_NAME,
                              }

def test_update_flow_missing_props(mock_connection, response_holder):
    props = copy.deepcopy(DEFAULT_PROPS)
    del props["Name"]
    assert schema_handler.try_handle(mock_connection, "Update", RESOURCE_TYPE, SCHEMA_NAME, props, response_holder)
    assert response_holder == {
                              "Status": "FAILED",
                              "Reason": 'Missing property "Name"',
                              "PhysicalResourceId": "unknown",
                              }


def test_update_simple(mock_connection, response_holder, mock_update):
    assert schema_handler.try_handle(mock_connection, "Update", RESOURCE_TYPE, SCHEMA_NAME, DEFAULT_PROPS, response_holder)
    mock_update.assert_called_once_with(mock_connection, SCHEMA_NAME, None, False, False, [], [], response_holder)


def test_delete_flow(mock_connection, response_holder):
    assert schema_handler.try_handle(mock_connection, "Delete", RESOURCE_TYPE, SCHEMA_NAME, DEFAULT_PROPS, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": SCHEMA_NAME,
                              }


def test_delete_flow_missing_props(mock_connection, response_holder):
    props = copy.deepcopy(DEFAULT_PROPS)
    del props["Name"]
    assert schema_handler.try_handle(mock_connection, "Delete", RESOURCE_TYPE, SCHEMA_NAME, props, response_holder)
    assert response_holder == {
                              "Status": "FAILED",
                              "Reason": 'Missing property "Name"',
                              "PhysicalResourceId": "unknown",
                              }


def test_delete(mock_connection, response_holder, mock_delete):
    assert schema_handler.try_handle(mock_connection, "Delete", RESOURCE_TYPE, SCHEMA_NAME, DEFAULT_PROPS, response_holder)
    mock_delete.assert_called_once_with(mock_connection, SCHEMA_NAME, True, response_holder)


def test_delete_ignores_name_property(mock_connection, response_holder, mock_delete):
    props = {
                "Name":       "anything",
            }
    assert schema_handler.try_handle(mock_connection, "Delete", RESOURCE_TYPE, SCHEMA_NAME, props, response_holder)
    mock_delete.assert_called_once_with(mock_connection, SCHEMA_NAME, False, response_holder)
