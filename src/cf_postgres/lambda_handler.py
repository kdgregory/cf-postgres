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
import requests
import sys
import uuid

from cf_postgres import util
import cf_postgres.handlers.testing as testing


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

HANDLERS = [ testing ]


def handle(event, context):
    print(json.dumps(event), file=sys.stderr)   # useful for debugging
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
        try_handlers(action, secret_arn, props, response)
    send_response(response_url, response)


def try_handlers(action, secret_arn, props, response):
    for handler in HANDLERS:
        if handler.try_handle(action, secret_arn, props, response):
            return
    LOGGER.error(f"unhandled action: {action}")
    response['Status'] = "FAILED"
    response['Reason'] = f"Unknown action: \"{action}\""


def send_response(response_url, response):
    LOGGER.info(f"sending response to {response_url}: {response}")
    rsp = requests.put(response_url, data=json.dumps(response))
    LOGGER.info(f"response status code: {rsp.status_code}")
