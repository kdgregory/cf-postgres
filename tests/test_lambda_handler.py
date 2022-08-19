import copy
import json
import unittest
from unittest.mock import Mock, MagicMock, patch, sentinel, ANY

from cf_postgres import lambda_handler
from cf_postgres.handlers import testing as test_handler


# event properties that will be asserted in response

EXPECTED_SERVICE_TOKEN  = "arn:aws:lambda:us-east-1:123456789012:function:cf_postgres"
EXPECTED_RESPONSE_URL   = "https://example.com/blahblahblah"
EXPECTED_STACK_ID       = "arn:aws:cloudformation:us-east-1:123456789012:stack/CF-Postgres-Example-4/388d1040-18a6-11ed-8d5d-0e8fec9940a1"
EXPECTED_REQUEST_ID     = "602e48af-49ab-4c5b-b856-95a2e84b66c9"
EXPECTED_LOGICAL_ID     = "TestHandler"
EXPECTED_PHYSICAL_ID    = "testing"
EXPECTED_SECRET_ARN     = "arn:aws:secretsmanager:us-east-1:123456789012:secret:database-1-admin-5z4FyE"

DEFAULT_EVENT           = {
                            "RequestType": "Create",
                            "ServiceToken": EXPECTED_SERVICE_TOKEN,
                            "ResponseURL": EXPECTED_RESPONSE_URL,
                            "StackId": EXPECTED_STACK_ID,
                            "RequestId": EXPECTED_REQUEST_ID,
                            "LogicalResourceId": EXPECTED_LOGICAL_ID,
                            "ResourceType": "Custom::CFPostgres-Database",
                            "ResourceProperties": {
                                "ServiceToken": EXPECTED_SERVICE_TOKEN,
                                "Action": "Testing",
                                "SecretArn": EXPECTED_SECRET_ARN,
                                "TestResourceName": EXPECTED_PHYSICAL_ID
                            }
                          }


class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_connection.__enter__ = Mock(return_value=sentinel.connection)
        self.mock_connection.__exit__ = Mock(return_value=False)
        self.open_connection_mock = Mock(return_value=self.mock_connection)
        self.send_response_mock = Mock()


    def invoke_lambda(self, event):
        with patch.object(lambda_handler, 'open_connection', self.open_connection_mock):
            with patch.object(lambda_handler, 'send_response', self.send_response_mock):
                lambda_handler.handle(event, None)


    def test_happy_path(self):
        event = copy.deepcopy(DEFAULT_EVENT)
        self.invoke_lambda(event)
        self.open_connection_mock.assert_called_once_with(
            EXPECTED_SECRET_ARN)
        self.assertEqual(test_handler.saved_connection, sentinel.connection)
        self.send_response_mock.assert_called_once_with(
            EXPECTED_RESPONSE_URL,
            {
                "Status": "SUCCESS",
                "StackId": EXPECTED_STACK_ID,
                "RequestId": EXPECTED_REQUEST_ID,
                "LogicalResourceId": EXPECTED_LOGICAL_ID,
                "PhysicalResourceId": EXPECTED_PHYSICAL_ID,
            })


    def test_unknown_action(self):
        event = copy.deepcopy(DEFAULT_EVENT)
        event["ResourceProperties"]["Action"] = "Bogus"
        self.invoke_lambda(event)
        self.open_connection_mock.assert_called_once_with(EXPECTED_SECRET_ARN)
        self.send_response_mock.assert_called_once_with(EXPECTED_RESPONSE_URL, {
            "Status": "FAILED",
            "Reason": ANY,
            "StackId": EXPECTED_STACK_ID,
            "RequestId": EXPECTED_REQUEST_ID,
            "LogicalResourceId": EXPECTED_LOGICAL_ID,
            "PhysicalResourceId": ANY,
        })
        actual_reason = self.send_response_mock.mock_calls[0][1][1]["Reason"]
        self.assertTrue("Unknown action" in actual_reason, f"(actual reason: {actual_reason})")
        self.assertTrue("Bogus" in actual_reason, f"(actual reason: {actual_reason})")


    def test_missing_action(self):
        event = copy.deepcopy(DEFAULT_EVENT)
        del event["ResourceProperties"]["Action"]
        self.invoke_lambda(event)
        self.open_connection_mock.assert_not_called()
        self.send_response_mock.assert_called_once_with(EXPECTED_RESPONSE_URL, {
            "Status": "FAILED",
            "Reason": ANY,
            "StackId": EXPECTED_STACK_ID,
            "RequestId": EXPECTED_REQUEST_ID,
            "LogicalResourceId": EXPECTED_LOGICAL_ID,
            "PhysicalResourceId": ANY,
        })
        actual_reason = self.send_response_mock.mock_calls[0][1][1]["Reason"]
        self.assertTrue("Action" in actual_reason, f"(actual reason: {actual_reason})")


    def test_missing_secret_arn(self):
        event = copy.deepcopy(DEFAULT_EVENT)
        del event["ResourceProperties"]["SecretArn"]
        self.invoke_lambda(event)
        self.open_connection_mock.assert_not_called()
        self.send_response_mock.assert_called_once_with(EXPECTED_RESPONSE_URL, {
            "Status": "FAILED",
            "Reason": ANY,
            "StackId": EXPECTED_STACK_ID,
            "RequestId": EXPECTED_REQUEST_ID,
            "LogicalResourceId": EXPECTED_LOGICAL_ID,
            "PhysicalResourceId": ANY,
        })
        actual_reason = self.send_response_mock.mock_calls[0][1][1]["Reason"]
        self.assertTrue("SecretArn" in actual_reason, f"(actual reason: {actual_reason})")
