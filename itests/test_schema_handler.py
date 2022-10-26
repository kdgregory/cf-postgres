import copy
import json
import pytest
import random
from unittest.mock import Mock, patch, ANY

import pg8000.dbapi

from cf_postgres import util, itest_helpers
from cf_postgres.handlers import schema_handler

################################################################################
## fixtures
################################################################################

@pytest.fixture
def randval():
    return random.randrange(100000, 999999)


@pytest.fixture
def schema_name(randval):
    return f"schema_{randval}"


@pytest.fixture
def response(randval):
    return {}


@pytest.fixture
def shared_connection():
    return util.connect_to_db(itest_helpers.local_pg8000_secret(None))


@pytest.fixture
def db_admin():
    return itest_helpers.local_pg8000_secret(None)["user"]


################################################################################
# Expected permissions, so that assertions aren't filled with boilerplate
################################################################################

PERM_SCHEMA_CREATE      = itest_helpers.Permission("CREATE")    # for schema-level permissions we don't specify object type
PERM_SCHEMA_USAGE       = itest_helpers.Permission("USAGE")

PERM_TABLE_DELETE       = itest_helpers.Permission('DELETE',      'r', False)
PERM_TABLE_INSERT       = itest_helpers.Permission('INSERT',      'r', False)
PERM_TABLE_REFERENCES   = itest_helpers.Permission('REFERENCES',  'r', False)
PERM_TABLE_SELECT       = itest_helpers.Permission('SELECT',      'r', False)
PERM_TABLE_TRIGGER      = itest_helpers.Permission('TRIGGER',     'r', False)
PERM_TABLE_TRUNCATE     = itest_helpers.Permission('TRUNCATE',    'r', False)
PERM_TABLE_UPDATE       = itest_helpers.Permission('UPDATE',      'r', False)

PERM_SEQUENCE_SELECT    = itest_helpers.Permission('SELECT',      'S', False)
PERM_SEQUENCE_UPDATE    = itest_helpers.Permission('UPDATE',      'S', False)
PERM_SEQUENCE_USAGE     = itest_helpers.Permission('USAGE',       'S', False)

PERM_FUNCTION_EXECUTE   = itest_helpers.Permission('EXECUTE',     'f', False)

PERM_TYPE_USAGE         = itest_helpers.Permission('USAGE',       'T', False)


################################################################################
## helper functions
################################################################################

def assert_schema(schema_name, owner_name, privs_by_grantee, default_privs):
    info = itest_helpers.retrieve_schema_info(schema_name)
    assert len(info) == 1
    assert info[0]["owner_name"] == owner_name
    assert itest_helpers.retrieve_schema_permissions(schema_name) == privs_by_grantee
    assert itest_helpers.retrieve_default_schema_permissions(schema_name) == default_privs

################################################################################
## Testcases
################################################################################

def test_create_default_owner_no_explicit_acls(db_admin, schema_name, response):
    props = {
            "Name":     schema_name,
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Create", "Schema", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": schema_name,
                       }
    assert_schema(schema_name, db_admin,  {}, {})    # grants are blank until first explicit grant


def test_create_default_owner_public_access(db_admin, schema_name, response):
    props = {
            "Name":     schema_name,
            "Public":   "true",
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Create", "Schema", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": schema_name,
                       }
    assert_schema(schema_name, db_admin,
                  {
                      db_admin: set([PERM_SCHEMA_USAGE, PERM_SCHEMA_CREATE]),   # adding any grants adds owner grant
                      "PUBLIC": set([PERM_SCHEMA_USAGE, PERM_SCHEMA_CREATE]),
                  },
                  {
                      # schema owner always has full privileges
                      "PUBLIC": set([PERM_TABLE_INSERT, PERM_TABLE_SELECT, PERM_TABLE_UPDATE, PERM_TABLE_DELETE,
                                    PERM_TABLE_TRUNCATE, PERM_TABLE_REFERENCES, PERM_TABLE_TRIGGER,
                                    PERM_SEQUENCE_SELECT, PERM_SEQUENCE_UPDATE, PERM_SEQUENCE_USAGE,
                                    PERM_FUNCTION_EXECUTE,
                                    PERM_TYPE_USAGE,
                                    ]),
                  })


def test_create_default_owner_public_readonly_access(db_admin, schema_name, response):
    props = {
            "Name":     schema_name,
            "ReadOnly":   "true",
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Create", "Schema", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": schema_name,
                       }
    assert_schema(schema_name, db_admin,
                  {
                      db_admin: set([PERM_SCHEMA_USAGE, PERM_SCHEMA_CREATE]),   # adding any grants adds owner grant
                      "PUBLIC": set([PERM_SCHEMA_USAGE]),
                  },
                  {
                      # schema owner always has full privileges
                      "PUBLIC": set([PERM_TABLE_SELECT,
                                    PERM_SEQUENCE_SELECT, PERM_SEQUENCE_USAGE,
                                    PERM_FUNCTION_EXECUTE,
                                    ]),
                  })


def test_create_default_owner_explicit_user_acls(randval, db_admin, schema_name, response):
    user_1 = itest_helpers.create_user(f"user_{randval}_1")
    user_2 = itest_helpers.create_user(f"user_{randval}_2")
    props = {
            "Name":             schema_name,
            "Users":            [ user_1 ],
            "ReadOnlyUsers":    [ user_2 ]
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Create", "Schema", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": schema_name,
                       }
    assert_schema(schema_name, db_admin,
                  {
                      db_admin: set([PERM_SCHEMA_USAGE, PERM_SCHEMA_CREATE]),
                      user_1:   set([PERM_SCHEMA_USAGE, PERM_SCHEMA_CREATE]),
                      user_2:   set([PERM_SCHEMA_USAGE]),
                  },
                  {
                      # schema owner always has full privileges
                      user_1:   set([PERM_TABLE_INSERT, PERM_TABLE_SELECT, PERM_TABLE_UPDATE, PERM_TABLE_DELETE,
                                    PERM_TABLE_TRUNCATE, PERM_TABLE_REFERENCES, PERM_TABLE_TRIGGER,
                                    PERM_SEQUENCE_SELECT, PERM_SEQUENCE_UPDATE, PERM_SEQUENCE_USAGE,
                                    PERM_FUNCTION_EXECUTE,
                                    PERM_TYPE_USAGE,
                                    ]),
                      user_2:   set([PERM_TABLE_SELECT,
                                    PERM_SEQUENCE_SELECT, PERM_SEQUENCE_USAGE,
                                    PERM_FUNCTION_EXECUTE,
                                    ]),
                  })


def test_create_default_owner_mixed_public_and_user_acls(randval, db_admin, schema_name, response):
    user_1 = itest_helpers.create_user(f"user_{randval}_1")
    user_2 = itest_helpers.create_user(f"user_{randval}_2")
    props = {
            "Name":             schema_name,
            "ReadOnly":         "true",
            "Users":            [ user_1 ],
            "ReadOnlyUsers":    [ user_2 ]
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Create", "Schema", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": schema_name,
                       }
    assert_schema(schema_name, db_admin,
                  {
                      db_admin: set([PERM_SCHEMA_USAGE, PERM_SCHEMA_CREATE]),
                      "PUBLIC": set([PERM_SCHEMA_USAGE]),
                      user_1:   set([PERM_SCHEMA_USAGE, PERM_SCHEMA_CREATE]),
                      user_2:   set([PERM_SCHEMA_USAGE]),
                  },
                  {
                      # schema owner always has full privileges
                      "PUBLIC": set([PERM_TABLE_SELECT,
                                    PERM_SEQUENCE_SELECT, PERM_SEQUENCE_USAGE,
                                    PERM_FUNCTION_EXECUTE,
                                    ]),
                      user_1:   set([PERM_TABLE_INSERT, PERM_TABLE_SELECT, PERM_TABLE_UPDATE, PERM_TABLE_DELETE,
                                    PERM_TABLE_TRUNCATE, PERM_TABLE_REFERENCES, PERM_TABLE_TRIGGER,
                                    PERM_SEQUENCE_SELECT, PERM_SEQUENCE_UPDATE, PERM_SEQUENCE_USAGE,
                                    PERM_FUNCTION_EXECUTE,
                                    PERM_TYPE_USAGE,
                                    ]),
                      user_2:   set([PERM_TABLE_SELECT,
                                    PERM_SEQUENCE_SELECT, PERM_SEQUENCE_USAGE,
                                    PERM_FUNCTION_EXECUTE,
                                    ]),
                  })


# we'll just verify that we can specify owner; the ACLs are handled separately so no need to replicate above tests
def test_create_explicit_owner_no_explicit_acls(randval, schema_name, response):
    owner = itest_helpers.create_user(f"user_{randval}_0")
    props = {
            "Name":     schema_name,
            "Owner":    owner,
            }
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Create", "Schema", None, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": schema_name,
                       }
    assert_schema(schema_name, owner, {}, {})    # grants are blank until first explicit grant


def test_delete(randval, db_admin, schema_name, response):
    props = {
            "Name":     schema_name
            }
    # first create the schema and verify that it's there
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Create", "Schema", None, props, {}, response)
    assert_schema(schema_name, db_admin, {}, {})
    # then delete and verify that it's no longer there
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Delete", "Schema", schema_name, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": schema_name,
                       }
    assert len(itest_helpers.retrieve_schema_info(schema_name)) == 0


def test_delete_cascade(randval, db_admin, schema_name, response):
    props = {
            "Name":     schema_name,
            "Cascade":  "true"
            }
    # first create the schema, along with a table inside it
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Create", "Schema", None, props, {}, response)
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        csr = conn.cursor()
        csr.execute(f"create table {schema_name}.t{randval} ( x int not null )")
        conn.commit()
    # then delete and verify that it's no longer there
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Delete", "Schema", schema_name, props, {}, response)
    assert response == {
                       "Status": "SUCCESS",
                       "PhysicalResourceId": schema_name,
                       }
    assert len(itest_helpers.retrieve_schema_info(schema_name)) == 0


def test_delete_failure_no_cascade(randval, db_admin, schema_name, response):
    props = {
            "Name":     schema_name,
            }
    # first create the schema, along with a table inside it
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Create", "Schema", None, props, {}, response)
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        csr = conn.cursor()
        csr.execute(f"create table {schema_name}.t{randval} ( x int not null )")
        conn.commit()
    # then attempt to delete
    with util.connect_to_db(itest_helpers.local_pg8000_secret(None)) as conn:
        assert schema_handler.try_handle(conn, "Delete", "Schema", schema_name, props, {}, response)
    assert response == {
                       "Status": "FAILED",
                       "PhysicalResourceId": schema_name,
                       "Reason": ANY
                       }
    # and verify that it's still there
    assert len(itest_helpers.retrieve_schema_info(schema_name)) == 1
