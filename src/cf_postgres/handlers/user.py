""" The CreateUser handler.
    """

import sys

from cf_postgres import util

# the allowed properties
PROP_USERNAME = "Username"
PROP_PASSWORD = "Password"


def try_handle(action, request_type, conn, props, response):
    if action != "CreateUser":
        return False
    (username, password) = load_user_info(props, response)
    if username:
        handle(request_type, conn, props, username, password, response)
    return True


def load_user_info(props, response):
    """ Attempts to retrieve user information, either from the properties
        or a referenced secret. Returns None is unable to do so, and sets
        failure information in the response.
        """
    username = util.verify_property(props, response, PROP_USERNAME )
    password = props.get(PROP_PASSWORD)
    if username:
        return (username, password)
    else:
        return None


def handle(request_type, conn, props, username, password, response):
    try:
        if request_type == "Create":
            doCreate(username, password, props, response)
        elif request_type == "Update":
            doUpdate(username, props, response)
        elif request_type == "Delete":
            doDelete(username, props, response)
        else:
            util.report_failure(response, f"Unknown request type: {request_type}")
    except:
            util.report_failure(response, str(sys.exc_info()[1]))


def doCreate(username, password, props, response):
    util.report_success(response, username)


def doUpdate(username, props, response):
    util.report_failure(response, "Can not update a user once created")
    response['PhysicalResourceId'] = "unknown"


def doDelete(username, props, response):
    util.report_success(response, username)
