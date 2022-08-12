""" A dummy handler used for unit tests.
    """

def try_handle(action, secret_arn, props, response):
    if action != "Testing":
        return False
    response['Status']             = "SUCCESS"
    response['PhysicalResourceId'] = props.get("TestResourceName")
    return True
