""" Integration tests for the CreateUser action: creates and verifies a user in a
    local database. ** Does not clean up afterward **
    """

import copy
import pytest
import random
from unittest.mock import Mock, patch, ANY

import pg8000.dbapi

from cf_postgres import util, itest_helpers
from cf_postgres.handlers import user_handler

################################################################################
## fixtures
################################################################################

@pytest.fixture
def randval():
    return random.randrange(100000, 999999)


@pytest.fixture
def username(randval):
    return f"user_{randval}"


@pytest.fixture
def password(randval):
    return f"pass_{randval}"


@pytest.fixture
def response(randval):
    return {}

################################################################################
## helper functions
################################################################################

def assert_user_info(username, has_createdb, has_createrole):
    user_info = itest_helpers.retrieve_user_info(username)
    assert user_info != None
    assert user_info['rolcreatedb'] == has_createdb
    assert user_info['rolcreaterole'] == has_createrole


def assert_user_can_login(username, password):
    # for users with passwords, this is the gold-standard test
    connection_info = copy.deepcopy(itest_helpers.local_pg8000_secret(None))
    connection_info['user'] = username
    connection_info['password'] = password
    with pg8000.dbapi.connect(**connection_info) as conn:
        pass # success! (failure will throw)

################################################################################
## testcases
################################################################################

def test_create_from_username_and_password_no_extra_abilities(username, password, response):
    props = {
            "Username":     username,
            "Password":     password,
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert user_handler.try_handle(conn, "Create", "User", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": username,
                       }
    assert_user_info(username, False, False)
    assert_user_can_login(username, password)


def test_create_from_username_and_password_with_createdb(username, password, response):
    props = {
            "Username":         username,
            "Password":         password,
            "CreateDatabase":   "true",
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert user_handler.try_handle(conn, "Create", "User", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": username,
                       }
    assert_user_info(username, True, False)
    assert_user_can_login(username, password)


def test_create_from_username_and_password_with_createrole(username, password, response):
    props = {
            "Username":         username,
            "Password":         password,
            "CreateRole":       "true",
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert user_handler.try_handle(conn, "Create", "User", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": username,
                       }
    assert_user_info(username, False, True)
    assert_user_can_login(username, password)


def test_create_from_username_and_password_explicit_no_extra_abilities(username, password, response):
    props = {
            "Username":         username,
            "Password":         password,
            "CreateDatabase":   "false",
            "CreateRole":       "false",
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert user_handler.try_handle(conn, "Create", "User", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": username,
                       }
    assert_user_info(username, False, False)
    assert_user_can_login(username, password)


def test_create_from_username_only(username, response):
    props = {
            "Username":     username,
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert user_handler.try_handle(conn, "Create", "User", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": username,
                       }
    assert_user_info(username, False, False)
    # can't assert login because there's no password


def test_update(username, password, response):
    # we'll create the user with nothing, and then update
    test_create_from_username_only(username, response)
    props = {
            "Username":         username,
            "Password":         password,
            "CreateDatabase":   "true",
            "CreateRole":       "true",
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert user_handler.try_handle(conn, "Update", "User", username, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": username,
                       }
    assert_user_info(username, True, True)
    assert_user_can_login(username, password)


def test_delete(username, response):
    props = {
            "Username":     username,
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        csr = conn.cursor()
        csr.execute(f"create user {username} password NULL")
        conn.commit()
    assert itest_helpers.retrieve_user_info(username) != None   # verify that we created before trying to delete
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert user_handler.try_handle(conn, "Delete", "User", username, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": username,
                       }
    assert itest_helpers.retrieve_user_info(username) == None
