""" A dummy handler used for unit tests.
    """

from cf_postgres import util


def try_handle(conn, request_type, resource_type, physical_id, props, response):
    if resource_type != "Testing":
        return False
    global saved_request_type, saved_connection
    saved_request_type = request_type
    saved_connection = conn
    util.report_success(response, props.get("TestResourceName"))
    return True
