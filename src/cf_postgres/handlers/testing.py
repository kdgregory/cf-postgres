""" A dummy handler used for unit tests.
    """

saved_connection = None

def try_handle(action, conn, props, response):
    if action != "Testing":
        return False
    global saved_connection
    saved_connection = conn
    response['Status']             = "SUCCESS"
    response['PhysicalResourceId'] = props.get("TestResourceName")
    return True
