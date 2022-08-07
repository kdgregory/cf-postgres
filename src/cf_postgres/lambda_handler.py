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

from cf_request import util


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

PHYSICAL_ID = str(uuid.uuid4())


def handle(event, context):
    print(json.dumps(event), file=sys.stderr)   # useful for debugging

    response_url = event['ResponseURL']

    response = {
        'RequestId':            event['RequestId'],
        'StackId':              event['StackId'],
        'LogicalResourceId':    event['LogicalResourceId'],
    }

    action = util.verify_property(request, response, 'Action')
    secret_arn = util.verify_property(get'SecretArn')

    if action and secret_arn:
        # TODO - dispatch
        response['Status']             = "SUCCESS"
        response['PhysicalResourceId'] = PHYSICAL_ID

    LOGGER.info(f"sending response to {response_url}: {response}")
    rsp = requests.put(response_url, data=json.dumps(response))
    LOGGER.info(f"response status code: {rsp.status_code}")
