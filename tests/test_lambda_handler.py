import copy
import json
import pytest

from unittest.mock import Mock, MagicMock, patch, sentinel, ANY

from cf_postgres import lambda_handler
from cf_postgres.handlers import test_handler


################################################################################
## event properties that will be asserted in response
################################################################################


EXPECTED_REQUEST_TYPE   = "Create"
EXPECTED_SERVICE_TOKEN  = "arn:aws:lambda:us-east-1:123456789012:function:cf_postgres"
EXPECTED_RESPONSE_URL   = "https://example.com/blahblahblah"
EXPECTED_STACK_ID       = "arn:aws:cloudformation:us-east-1:123456789012:stack/CF-Postgres-Example-4/388d1040-18a6-11ed-8d5d-0e8fec9940a1"
EXPECTED_REQUEST_ID     = "602e48af-49ab-4c5b-b856-95a2e84b66c9"
EXPECTED_LOGICAL_ID     = "TestHandler"
EXPECTED_PHYSICAL_ID    = "testing"
EXPECTED_SECRET_ARN     = "arn:aws:secretsmanager:us-east-1:123456789012:secret:database-1-admin-5z4FyE"


################################################################################
## fixtures
################################################################################


@pytest.fixture
def event():
    return {
        "RequestType": EXPECTED_REQUEST_TYPE,
        "ServiceToken": EXPECTED_SERVICE_TOKEN,
        "ResponseURL": EXPECTED_RESPONSE_URL,
        "StackId": EXPECTED_STACK_ID,
        "RequestId": EXPECTED_REQUEST_ID,
        "LogicalResourceId": EXPECTED_LOGICAL_ID,
        "ResourceType": "Custom::CFPostgres",
        "ResourceProperties": {
            "ServiceToken": EXPECTED_SERVICE_TOKEN,
            "Resource": "Testing",
            "AdminSecretArn": EXPECTED_SECRET_ARN,
            "TestResourceName": EXPECTED_PHYSICAL_ID
        }
      }


@pytest.fixture
def mock_connection():
    mock_connection = MagicMock()
    mock_connection.__enter__ = Mock(return_value=sentinel.connection)
    mock_connection.__exit__ = Mock(return_value=False)
    return mock_connection


@pytest.fixture
def open_connection_mock(mock_connection):
    return Mock(return_value=mock_connection)


@pytest.fixture
def send_response_mock():
    return Mock()


@pytest.fixture
def patched_lambda(monkeypatch, open_connection_mock, send_response_mock):
    monkeypatch.setattr(lambda_handler, 'open_connection', open_connection_mock)
    monkeypatch.setattr(lambda_handler, 'send_response', send_response_mock)


################################################################################
## testcases
################################################################################


def test_happy_path(patched_lambda, event, open_connection_mock, send_response_mock):
    lambda_handler.handle(event, None)
    open_connection_mock.assert_called_once_with(EXPECTED_SECRET_ARN)
    assert test_handler.saved_request_type == EXPECTED_REQUEST_TYPE
    assert test_handler.saved_connection == sentinel.connection
    send_response_mock.assert_called_once_with(
        EXPECTED_RESPONSE_URL,
        {
            "Status": "SUCCESS",
            "StackId": EXPECTED_STACK_ID,
            "RequestId": EXPECTED_REQUEST_ID,
            "LogicalResourceId": EXPECTED_LOGICAL_ID,
            "PhysicalResourceId": EXPECTED_PHYSICAL_ID,
        })


def test_unknown_resource(patched_lambda, event, open_connection_mock, send_response_mock):
    event["ResourceProperties"]["Resource"] = "Bogus"
    lambda_handler.handle(event, None)
    open_connection_mock.assert_called_once_with(EXPECTED_SECRET_ARN)
    send_response_mock.assert_called_once_with(EXPECTED_RESPONSE_URL, {
        "Status": "FAILED",
        "Reason": ANY,
        "StackId": EXPECTED_STACK_ID,
        "RequestId": EXPECTED_REQUEST_ID,
        "LogicalResourceId": EXPECTED_LOGICAL_ID,
        "PhysicalResourceId": ANY,
    })
    actual_reason = send_response_mock.mock_calls[0][1][1]["Reason"]
    assert "Unknown resource" in actual_reason
    assert "Bogus" in actual_reason


def test_missing_resource(patched_lambda, event, open_connection_mock, send_response_mock):
    del event["ResourceProperties"]["Resource"]
    lambda_handler.handle(event, None)
    open_connection_mock.assert_not_called()
    send_response_mock.assert_called_once_with(EXPECTED_RESPONSE_URL, {
        "Status": "FAILED",
        "Reason": ANY,
        "StackId": EXPECTED_STACK_ID,
        "RequestId": EXPECTED_REQUEST_ID,
        "LogicalResourceId": EXPECTED_LOGICAL_ID,
        "PhysicalResourceId": ANY,
    })
    assert "Resource" in send_response_mock.mock_calls[0][1][1]["Reason"]


def test_missing_secret_arn(patched_lambda, event, open_connection_mock, send_response_mock):
    del event["ResourceProperties"]["AdminSecretArn"]
    lambda_handler.handle(event, None)
    open_connection_mock.assert_not_called()
    send_response_mock.assert_called_once_with(EXPECTED_RESPONSE_URL, {
        "Status": "FAILED",
        "Reason": ANY,
        "StackId": EXPECTED_STACK_ID,
        "RequestId": EXPECTED_REQUEST_ID,
        "LogicalResourceId": EXPECTED_LOGICAL_ID,
        "PhysicalResourceId": ANY,
    })
    assert "SecretArn" in send_response_mock.mock_calls[0][1][1]["Reason"]


# the following tests verify that the resource handlers are properly configured
# they should all fail, but at least they'll try to handle the resource

def test_user_resource(patched_lambda, event, open_connection_mock, send_response_mock):
    event["ResourceProperties"]["Resource"] = "User"
    lambda_handler.handle(event, None)
    send_response_mock.assert_called_once_with(EXPECTED_RESPONSE_URL, {
        "Status": "FAILED",
        "Reason": ANY,
        "StackId": EXPECTED_STACK_ID,
        "RequestId": EXPECTED_REQUEST_ID,
        "LogicalResourceId": EXPECTED_LOGICAL_ID,
        "PhysicalResourceId": ANY,
    })
    assert "Unknown resource" not in send_response_mock.mock_calls[0][1][1]["Reason"]
