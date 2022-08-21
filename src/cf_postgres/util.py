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


""" Assorted utility functions.
    """

import boto3
import json
import logging
import os

from functools import lru_cache


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def verify_property(request, response, name):
    """ Attempts to retrieve a named property from the request object. If not present,
        it sets the failure fields on the response object. Caller is responsible to
        abort processing.
        """
    value = request.get(name)
    if value:
        LOGGER.debug(f"{name}: {value}")
        return value
    else:
        LOGGER.error(f"missing property \"{name}\"")
        report_failure(response, f"Missing property \"{name}\"")
        return None


def report_success(response, physical_resource_id, data=None):
    """ Populates the response for successful operation. Must include a valid
        resource ID, may include a dict of additional data that can be accessed
        via Fn::GetAtt.
        """
    response['Status']             = "SUCCESS"
    response['PhysicalResourceId'] = physical_resource_id
    if data:
        response['Data']           = data


def report_failure(response, reason, physical_resource_id=None):
    """ Populates the response for failed operation. Must include a reason; may
        include an actual resource ID, or will substitute with "unknown".
        """
    response['Status']              = "FAILED"
    response['Reason']              = reason
    response['PhysicalResourceId']  = physical_resource_id or "unknown"


@lru_cache(maxsize=1)
def retrieve_secret(secret_arn):
    """ Retrieves the named secret and parses its contents as JSON.
        """
    LOGGER.debug(f"retrieving secret: {secret_arn}")
    sm_client = boto3.client('secretsmanager')
    secret_json = sm_client.get_secret_value(SecretId=secret_arn)['SecretString']
    return json.loads(secret_json)


def retrieve_pg8000_secret(secret_arn):
    """ Retrieves the named secret and extracts the keyword arguments used for
        making a PG8000 connection.
        """
    secret = retrieve_secret(secret_arn)
    return {
        'user':             secret['username'],
        'password':         secret['password'],
        'host':             secret['host'],
        'database':         secret['dbname'],
        'port':             int(secret['port']),
        'application_name': "cf-postgres",
    }
