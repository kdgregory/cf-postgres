""" Unit tests for the Schema sub-resource. These tests verify the behavior of
    the handler, but do not attempt to verify that it executed the correct SQL.
    Some tests mock out the internal action methods to verify that they've been
    called correctly, while others check the overall flow by looking at the
    response object.
    """

import copy
import json
import pytest
from unittest.mock import Mock, call, patch, ANY

from cf_postgres import util
from cf_postgres.handlers import schema_handler
from more_itertools.more import side_effect


################################################################################
# properties from the default event
################################################################################

RESOURCE_TYPE       = "Schema"
ADMIN_SECRET_ARN    = "arn:aws:secretsmanager:us-east-1:123456789012:secret:database-1-admin-5z4FyE"
SCHEMA_NAME         = "example"
OWNER               = "me"
USERS               = ["argle", "bargle"]
RO_USERS            = ["foo", "bar", "baz"]

IS_PUBLIC           = True
IS_PUBLIC_STR       = "true"
IS_READONLY         = False
IS_READONLY_STR     = "false"
CASCADE             = False
CASCADE_STR         = "true"

################################################################################
## fixtures
################################################################################

@pytest.fixture
def mock_connection():
    return Mock()


@pytest.fixture
def default_props():
    # the tests just check equality; modify or delete as desired
    return {
        'Name':             SCHEMA_NAME,
        'Owner':            OWNER,
        'Public':           IS_PUBLIC_STR,
        'ReadOnly':         IS_READONLY_STR,
        'Users':            USERS,
        'ReadOnlyUsers':    RO_USERS,
        "Cascade":          CASCADE_STR,
        }


@pytest.fixture
def response_holder():
    return {}


@pytest.fixture
def extract_props_spy(monkeypatch):
    spy = Mock(side_effect=schema_handler._extract_props)
    monkeypatch.setattr(schema_handler, '_extract_props', spy)
    return spy


@pytest.fixture
def do_create_spy(monkeypatch):
    spy = Mock(side_effect=schema_handler._doCreate)
    monkeypatch.setattr(schema_handler, '_doCreate', spy)
    return spy


@pytest.fixture
def do_update_spy(monkeypatch):
    spy = Mock(side_effect=schema_handler._doUpdate)
    monkeypatch.setattr(schema_handler, '_doUpdate', spy)
    return spy


@pytest.fixture
def do_delete_spy(monkeypatch):
    spy = Mock(side_effect=schema_handler._doDelete)
    monkeypatch.setattr(schema_handler, '_doDelete', spy)
    return spy


################################################################################
## testcases
##
## these tests dig into the internals of the handler more than "unit" tests
## should ... I suppose I could just let them exercise the class and leave
## everything else to the integration tests, but :shrug:
################################################################################

def test_extract_props(default_props):
    (owner_name, is_public, is_readonly, users, ro_users) = schema_handler._extract_props(default_props)
    assert owner_name == OWNER
    assert is_public == IS_PUBLIC
    assert is_readonly == IS_READONLY
    assert users == USERS
    assert ro_users == RO_USERS
        

def test_create_happy_path(monkeypatch, mock_connection, extract_props_spy, do_create_spy, do_update_spy, do_delete_spy, default_props, response_holder):
    assert schema_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, default_props, {}, response_holder)
    do_create_spy.assert_called_once_with(mock_connection, SCHEMA_NAME, default_props, response_holder)
    do_update_spy.assert_not_called()
    do_delete_spy.assert_not_called()
    extract_props_spy.assert_called_once_with(default_props)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": SCHEMA_NAME,
                              }        

def test_update_happy_path(monkeypatch, mock_connection, extract_props_spy, do_create_spy, do_update_spy, do_delete_spy, default_props, response_holder):
    old_props = copy.deepcopy(default_props)
    old_props['Users'] = RO_USERS
    old_props['ReadOnlyUsers'] = USERS
    assert schema_handler.try_handle(mock_connection, "Update", RESOURCE_TYPE, SCHEMA_NAME, default_props, old_props, response_holder)
    do_create_spy.assert_not_called()
    do_update_spy.assert_called_once_with(mock_connection, SCHEMA_NAME, SCHEMA_NAME, default_props, old_props, response_holder)
    do_delete_spy.assert_not_called()
    extract_props_spy.assert_has_calls([call(default_props), call(old_props)])
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": SCHEMA_NAME,
                              }
        

def test_delete_happy_path(monkeypatch, mock_connection, extract_props_spy, do_create_spy, do_update_spy, do_delete_spy, default_props, response_holder):
    assert schema_handler.try_handle(mock_connection, "Delete", RESOURCE_TYPE, SCHEMA_NAME, default_props, {}, response_holder)
    do_create_spy.assert_not_called()
    do_update_spy.assert_not_called()
    do_delete_spy.assert_called_once_with(mock_connection, SCHEMA_NAME, default_props, response_holder)
    assert response_holder == {
                              "Status": "SUCCESS",
                              "PhysicalResourceId": SCHEMA_NAME,
                              }    


def test_exception_in_action_method(monkeypatch, mock_connection, default_props, response_holder):
    mock = Mock(side_effect=Exception("I don't work!"))
    monkeypatch.setattr(schema_handler, '_doCreate', mock)
    assert schema_handler.try_handle(mock_connection, "Create", RESOURCE_TYPE, None, default_props, {}, response_holder)
    mock.assert_called_once_with(mock_connection, SCHEMA_NAME, default_props, response_holder)
    assert response_holder == {
                              "Status": "FAILED",
                              "PhysicalResourceId": ANY,
                              "Reason": ANY
                              } 