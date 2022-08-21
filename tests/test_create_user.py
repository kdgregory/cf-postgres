import copy
import json
import unittest
from unittest.mock import Mock, patch, ANY

from cf_postgres.handlers import user as user_handler


# event properties that will be asserted in response

ACTION              = "CreateUser"
USERNAME            = "tester"
PASSWORD            = "tester-123"
ADMIN_SECRET_ARN    = "arn:aws:secretsmanager:us-east-1:123456789012:secret:database-1-admin-5z4FyE"


class TestUserHandler(unittest.TestCase):

    def test_create_from_props(self):
        mock_connection = Mock()
        props = {
                    "Username":     USERNAME,
                    "Password":     PASSWORD
                }
        response = {}
        result = user_handler.try_handle(ACTION, "Create", mock_connection, props, response)
        self.assertTrue(result)
        self.assertEquals(response,
                          {
                            "Status": "SUCCESS",
                            "PhysicalResourceId": USERNAME,
                          })
