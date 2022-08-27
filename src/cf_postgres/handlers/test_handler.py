""" A dummy handler used for unit tests.
    """

from cf_postgres import util


def try_handle(action, request_type, conn, props, response):
    if action != "Testing":
        return False
    global saved_request_type, saved_connection
    saved_request_type = request_type
    saved_connection = conn
    util.report_success(response, props.get("TestResourceName"))
    return True
