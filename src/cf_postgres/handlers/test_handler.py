""" A dummy handler used for unit tests.
    """

from cf_postgres import util


def try_handle(resource, request_type, conn, props, response):
    if resource != "Testing":
        return False
    global saved_request_type, saved_connection
    saved_request_type = request_type
    saved_connection = conn
    util.report_success(response, props.get("TestResourceName"))
    return True
