# Copyright (c) Keith D Gregory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Entry-point for all operations. This handler will dispatch the event
    to a module that can handle it.
    """

import boto3
import json
import logging
import pg8000.dbapi
import requests
import sys
import uuid

from cf_postgres import util
import cf_postgres.handlers.testing as testing


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

HANDLERS = [ testing ]


def handle(event, context):
    # print(json.dumps(event), file=sys.stderr)   # useful for debugging
    response_url = event['ResponseURL']
    response = {
        'RequestId':            event['RequestId'],
        'StackId':              event['StackId'],
        'LogicalResourceId':    event['LogicalResourceId'],
        'PhysicalResourceId':   "to_be_populated",              # required, even for failure
    }
    props = event['ResourceProperties']
    action = util.verify_property(props, response, 'Action')
    secret_arn = util.verify_property(props, response, 'SecretArn')
    if action and secret_arn:
        try:
            with open_connection(secret_arn) as conn:
                try_handlers(action, conn, props, response)
        except Exception as ex:
            LOGGER.error("unhandled exception", exc_info=True)
            response['Status'] = "FAILED"
            response['Reason'] = f"Unhandled exception: \"{ex}\""
    send_response(response_url, response)


def open_connection(secret_arn):
    """ Establishes the connection to the database. Any exceptions are allowed
        to propagate.
        """
    connection_info = util.retrieve_pg8000_secret(secret_arn)
    return pg8000.dbapi.connect(**connection_info)


def try_handlers(action, conn, props, response):
    """ Runs through the list of handlers, returning once one handles the action.
        """
    for handler in HANDLERS:
        if handler.try_handle(action, conn, props, response):
            return
    LOGGER.error(f"unhandled action: {action}")
    response['Status'] = "FAILED"
    response['Reason'] = f"Unknown action: \"{action}\""


def send_response(response_url, response):
    LOGGER.info(f"sending response to {response_url}: {response}")
    rsp = requests.put(response_url, data=json.dumps(response))
    LOGGER.info(f"response status code: {rsp.status_code}")
