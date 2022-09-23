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


def try_handle(resource, request_type, conn, props, response):
    if resource != RESOURCE_NAME:
        return False
    (username, password, with_createdb, with_createrole) = load_user_info(props, response)
    if username:
        handle(request_type, conn, username, password, with_createdb, with_createrole, response)
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
    with_createdb = props.get(PROP_CREATEDB, "false").lower() == "true"
    with_createrole = props.get(PROP_CREATEROLE, "false").lower() == "true"
    if username:
        return (username, password, with_createdb, with_createrole)
    else:
        util.report_failure(response, "Must specify username or secret")
        return (None, None, None, None)


def handle(request_type, conn, username, password, with_createdb, with_createrole, response):
    logging.info(f"performing {request_type} for user {username}")
    try:
        if request_type == ACTION_CREATE:
            doCreate(conn, username, password, with_createdb, with_createrole, response)
        elif request_type == ACTION_UPDATE:
            doUpdate(conn, username, response)
        elif request_type == ACTION_DELETE:
            doDelete(conn, username, response)
        else:
            util.report_failure(response, f"Unknown request type: {request_type}")
    except:
            util.report_failure(response, f"failed to complete action {request_type} for user {username}: {sys.exc_info()[1]}")
            conn.rollback()


def doCreate(conn, username, password, with_createdb, with_createrole, response):
    csr = conn.cursor()
    createdb   = "CREATEDB" if with_createdb else "NOCREATEDB"
    createrole = "CREATEROLE" if with_createrole else "NOCREATEROLE"
    if password:
        csr.execute(f"create user {username} password '{password}' {createrole} {createdb}")
    else:
        csr.execute(f"create user {username} password NULL {createrole} {createdb}")
    conn.commit()
    util.report_success(response, username)


def doUpdate(conn, username, response):
    util.report_failure(response, "Can not update a user once created")
    response['PhysicalResourceId'] = username


def doDelete(conn, username, response):
    csr = conn.cursor()
    csr.execute(f"drop user {username}")
    conn.commit()
    util.report_success(response, username)
