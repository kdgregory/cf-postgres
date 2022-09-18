""" Handler for User resources.
    """

import logging
import sys

from cf_postgres import util


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

# resource configuration

RESOURCE_NAME = "User"

PROP_USERNAME = "Username"
PROP_PASSWORD = "Password"
PROP_SECRET   = "UserSecretArn"


def try_handle(resource, request_type, conn, props, response):
    if resource != RESOURCE_NAME:
        return False
    (username, password) = load_user_info(props, response)
    if username:
        handle(request_type, conn, username, password, response)
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
        username = secret.get('username')
        password = secret.get('password')
    else:
        username = props.get(PROP_USERNAME)
        password = props.get(PROP_PASSWORD)
    if username:
        return (username, password)
    else:
        util.report_failure(response, "Must specify username or secret")
        return (None, None)


def handle(request_type, conn, username, password, response):
    LOGGER.info(f"performing {request_type} for user {username}")
    try:
        if request_type == "Create":
            doCreate(conn, username, password, response)
        elif request_type == "Update":
            doUpdate(conn, username, response)
        elif request_type == "Delete":
            doDelete(conn, username, response)
        else:
            util.report_failure(response, f"Unknown request type: {request_type}")
    except:
            util.report_failure(response, f"failed to complete action {request_type} for user {username}: {sys.exc_info()[1]}")
            conn.rollback()


def doCreate(conn, username, password, response):
    csr = conn.cursor()
    if password:
        csr.execute(f"create user {username} password '{password}'")
    else:
        csr.execute(f"create user {username} password NULL")
    conn.commit()
    util.report_success(response, username)


def doUpdate(conn, username, response):
    util.report_failure(response, "Can not update a user once created")
    response['PhysicalResourceId'] = "unknown"


def doDelete(conn, username, response):
    csr = conn.cursor()
    csr.execute(f"drop user {username}")
    conn.commit()
    util.report_success(response, username)
