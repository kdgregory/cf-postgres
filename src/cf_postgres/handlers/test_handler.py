""" A dummy resource handler used for unit tests of the lambda handler.
    """

from cf_postgres import util


def try_handle(conn, request_type, resource_type, physical_id, props, old_props, response):
    if resource_type != "Testing":
        return False
    global saved_connection, saved_request_type, saved_resource_type, saved_physical_id, saved_props, saved_old_props
    saved_connection = conn
    saved_request_type = request_type
    saved_resource_type = resource_type
    saved_physical_id = physical_id
    saved_props = props
    saved_old_props = old_props
    util.report_success(response, props.get("TestResourceName"))
    return True
