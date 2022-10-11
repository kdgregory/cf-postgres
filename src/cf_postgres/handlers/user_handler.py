""" Handler for User resources.
    """

import logging
import sys

from cf_postgres import util
from cf_postgres.constants import *


# resource configuration

RESOURCE_NAME = "User"

PROP_USERNAME   = "Username"
PROP_PASSWORD   = "Password"
PROP_SECRET     = "UserSecretArn"
PROP_CREATEDB   = "CreateDatabase"
PROP_CREATEROLE = "CreateRole"


def try_handle(conn, request_type, resource_type, physical_id, props, response):
    if resource_type != RESOURCE_NAME:
        return False
    (username, password, with_createdb, with_createrole) = load_user_info(props, response)
    if username:
        handle(conn, request_type, physical_id, username, password, with_createdb, with_createrole, response)
    else:
        util.report_failure(response, "Must specify username or secret")
    return True


def load_user_info(props, response):
    """ Attempts to retrieve user information, either from the properties
        or a referenced secret. Returns a tuple of username and password
        if able, a tuple of None if not (and sets failure information in
        the response).
        """
    secret_arn = props.get(PROP_SECRET)
    if secret_arn:
        secret = util.retrieve_json_secret(secret_arn)
        username = secret.get(DB_SECRET_USERNAME)
        password = secret.get(DB_SECRET_PASSWORD)
    else:
        username = props.get(PROP_USERNAME)
        password = props.get(PROP_PASSWORD)
    with_createdb = util.get_boolean_prop(props, PROP_CREATEDB, False)
    with_createrole = util.get_boolean_prop(props, PROP_CREATEROLE, False)
    return (username, password, with_createdb, with_createrole)


def handle(conn, request_type, physical_id, username, password, with_createdb, with_createrole, response):
    logging.info(f"user_handler: performing {request_type} for user {username}, resource {physical_id}")
    try:
        if request_type == ACTION_CREATE:
            doCreate(conn, username, password, with_createdb, with_createrole, response)
        elif request_type == ACTION_UPDATE:
            if physical_id == username:
                doUpdate(conn, username, password, with_createdb, with_createrole, response)
            else:
                util.report_failure(response, "Can not update username", physical_id)
        elif request_type == ACTION_DELETE:
            doDelete(conn, physical_id, response)
        else:
            util.report_failure(response, f"user_handler: Unknown request type: {request_type}")
    except:
        util.report_failure(response, f"user_handler: failed to complete action {request_type} for user {username}: {sys.exc_info()[1]}")
        conn.rollback()


def doCreate(conn, username, password, with_createdb, with_createrole, response):
    logging.debug(f"user_handler.doCreate(): user {username}, with_createdb {with_createdb}, with_createrole {with_createrole}")
    csr = conn.cursor()
    createdb   = "CREATEDB" if with_createdb else "NOCREATEDB"
    createrole = "CREATEROLE" if with_createrole else "NOCREATEROLE"
    if password:
        csr.execute(f"create user {username} password '{password}' {createdb} {createrole}")
    else:
        csr.execute(f"create user {username} password NULL {createdb} {createrole}")
    conn.commit()
    util.report_success(response, username)


def doUpdate(conn, username, password, with_createdb, with_createrole, response):
    logging.debug(f"user_handler.doUpdate(): user {username}, with_createdb {with_createdb}, with_createrole {with_createrole}")
    csr = conn.cursor()
    createdb   = "CREATEDB" if with_createdb else "NOCREATEDB"
    createrole = "CREATEROLE" if with_createrole else "NOCREATEROLE"
    if password:
        csr.execute(f"alter user {username} password '{password}' {createrole} {createdb}")
    else:
        csr.execute(f"alter user {username} password NULL {createrole} {createdb}")
    conn.commit()
    util.report_success(response, username)


def doDelete(conn, username, response):
    logging.debug(f"user_handler.doDelete(): user {username}")
    csr = conn.cursor()
    csr.execute(f"drop user {username}")
    conn.commit()
    util.report_success(response, username)
