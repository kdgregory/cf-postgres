""" Unit tests for the CreateUser action. These tests verify the behavior of the handler,
    but do not attempt to verify that it executed the correct SQL.
    """

import copy
import json
import unittest
from unittest.mock import Mock, patch, ANY

from cf_postgres import util
from cf_postgres.handlers import user_handler


# event properties that will be asserted

RESOURCE            = "User"
USERNAME            = "tester"
PASSWORD            = "tester-123"
ADMIN_SECRET_ARN    = "arn:aws:secretsmanager:us-east-1:123456789012:secret:database-1-admin-5z4FyE"
SECRET_ARN          = "arn:aws:secretsmanager:us-east-1:123456789012:secret:database-1-user-9qqMq4"

# mock secret contents

SECRET_VALUE        = {
                        'username': USERNAME,
                        'password': PASSWORD,
                      }


class TestUserHandler(unittest.TestCase):

    def test_create_from_username(self):
        mock_connection = Mock()
        props = {
                    "Username":     USERNAME,
                    "Password":     PASSWORD
                }
        response = {}
        result = user_handler.try_handle(RESOURCE, "Create", mock_connection, props, response)
        self.assertTrue(result)
        self.assertEqual(response,
                          {
                            "Status": "SUCCESS",
                            "PhysicalResourceId": USERNAME,
                          })


    def test_create_from_secret(self):
        mock_connection = Mock()
        props = {
                    "SecretArn":    SECRET_ARN,
                }
        response = {}
        with patch.object(util, 'retrieve_json_secret', Mock(return_value=SECRET_VALUE)):
            result = user_handler.try_handle(RESOURCE, "Create", mock_connection, props, response)
        self.assertTrue(result)
        self.assertEqual(response,
                          {
                            "Status": "SUCCESS",
                            "PhysicalResourceId": USERNAME,
                          })


    def test_create_missing_props(self):
        mock_connection = Mock()
        props = {
                }
        response = {}
        result = user_handler.try_handle(RESOURCE, "Create", mock_connection, props, response)
        self.assertTrue(result)
        self.assertEqual(response,
                          {
                            "Status": "FAILED",
                            "Reason": "Must specify username or secret",
                            "PhysicalResourceId": "unknown",
                          })


    def test_update(self):
        mock_connection = Mock()
        props = {
                    "Username":     USERNAME,
                }
        response = {}
        result = user_handler.try_handle(RESOURCE, "Update", mock_connection, props, response)
        self.assertTrue(result)
        self.assertEqual(response,
                          {
                            "Status": "FAILED",
                            "Reason": "Can not update a user once created",
                            "PhysicalResourceId": "unknown",
                          })

    def test_delete_from_username(self):
        mock_connection = Mock()
        props = {
                    "Username":     USERNAME,
                }
        response = {}
        result = user_handler.try_handle(RESOURCE, "Delete", mock_connection, props, response)
        self.assertTrue(result)
        self.assertEqual(response,
                          {
                            "Status": "SUCCESS",
                            "PhysicalResourceId": USERNAME,
                          })


    def test_create_from_secret(self):
        mock_connection = Mock()
        props = {
                    "UserSecretArn":    SECRET_ARN,
                }
        response = {}
        with patch.object(util, 'retrieve_json_secret', Mock(return_value=SECRET_VALUE)):
            result = user_handler.try_handle(RESOURCE, "Delete", mock_connection, props, response)
        self.assertTrue(result)
        self.assertEqual(response,
                          {
                            "Status": "SUCCESS",
                            "PhysicalResourceId": USERNAME,
                          })


    def test_delete_missing_props(self):
        mock_connection = Mock()
        props = {
                }
        response = {}
        result = user_handler.try_handle(RESOURCE, "Delete", mock_connection, props, response)
        self.assertTrue(result)
        self.assertEqual(response,
                          {
                            "Status": "FAILED",
                            "Reason": "Must specify username or secret",
                            "PhysicalResourceId": "unknown",
                          })
