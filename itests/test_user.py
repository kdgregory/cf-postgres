""" Integration tests for the CreateUser action: creates and verifies a user in a
    local database. ** Does not clean up afterward **
    """

import copy
import json
import pytest
import random
from unittest.mock import Mock, patch, ANY

import pg8000.dbapi

from cf_postgres import util
from cf_postgres.handlers import user_handler
from cf_postgres.itest_helpers import local_pg8000_secret

################################################################################
## fixtures
################################################################################

@pytest.fixture
def randval():
    return random.randrange(100000, 999999)


@pytest.fixture
def username(randval):
    username = f"user_{randval}"


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

def retrieve_user_info(username):
    return util.select_as_dict(
                local_pg8000_secret(None),
                lambda c:  c.execute("select * from pg_user where usename = %s", (username,)))


def assert_user_can_login(username, password):
    # verify that we properly supplied the password
    connection_info = copy.deepcopy(local_pg8000_secret(None))
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
    with util.connect_to_db(local_pg8000_secret(None)) as conn:
        assert user_handler.try_handle("User", "Create", conn, props, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": username,
                       }
    assert len(retrieve_user_info(username)) == 1
    assert_user_can_login(username, password)


def test_create_from_username(username, response):
    props = {
                "Username":     username,
            }
    with util.connect_to_db(local_pg8000_secret(None)) as conn:
        assert user_handler.try_handle("User", "Create", conn, props, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": username,
                       }
    assert len(retrieve_user_info(username)) == 1
    # can't assert login because there's no password


def test_delete(username, response):
    props = {
                "Username":     username,
            }
    with util.connect_to_db(local_pg8000_secret(None)) as conn:
        csr = conn.cursor()
        csr.execute(f"create user {username} password NULL")
        conn.commit()
    assert len(retrieve_user_info(username)) == 1   # verify that we created before trying to delete
    with util.connect_to_db(local_pg8000_secret(None)) as conn:
        assert user_handler.try_handle("User", "Delete", conn, props, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": username,
                       }
    assert len(retrieve_user_info(username)) == 0
