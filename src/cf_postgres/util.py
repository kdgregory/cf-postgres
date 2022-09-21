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
import time

import pg8000.dbapi

from cf_postgres.constants import *


def verify_property(request, response, name):
    """ Attempts to retrieve a named property from the request object. If not present,
        it sets the failure fields on the response object. Caller is responsible to
        abort processing.
        """
    value = request.get(name)
    if value:
        logging.debug(f"{name}: {value}")
        return value
    else:
        report_failure(response, f"Missing property \"{name}\"")
        return None


def report_success(response, physical_resource_id, data=None):
    """ Populates the response for successful operation. Must include a valid
        resource ID, may include a dict of additional data that can be accessed
        via Fn::GetAtt.
        """
    response[RSP_STATUS]        = RSP_SUCCESS
    response[RSP_PHYSICAL_ID]   = physical_resource_id
    if data:
        response[RSP_DATA]      = data


def report_failure(response, reason, physical_resource_id=None):
    """ Populates the response for failed operation. Must include a reason; may
        include an actual resource ID, or will substitute with "unknown".
        """
    logging.error(f"request failed: {reason}", exc_info=True)
    response[RSP_STATUS]        = RSP_FAILURE
    response[RSP_REASON]        = reason
    response[RSP_PHYSICAL_ID]   = physical_resource_id or "unknown"


def retrieve_json_secret(secret_arn):
    """ Retrieves the named secret and parses its contents as JSON.
        """
    logging.debug(f"retrieving secret: {secret_arn}")
    sm_client = boto3.client('secretsmanager')
    secret_json = sm_client.get_secret_value(SecretId=secret_arn)['SecretString']
    return json.loads(secret_json)


def retrieve_pg8000_secret(secret_arn):
    """ Retrieves the named secret, which is presumed to contain standard RDS
        connection information, and extracts the keyword arguments used for a
        PG8000 connection.
        """
    secret = retrieve_json_secret(secret_arn)
    return {
        'user':             secret[DB_SECRET_USERNAME],
        'password':         secret[DB_SECRET_PASSWORD],
        'host':             secret[DB_SECRET_HOSTNAME],
        'port':             int(secret[DB_SECRET_PORT]),
        'database':         secret[DB_SECRET_DATABASE],
        'application_name': "cf-postgres",
    }


def connect_to_db(connection_info):
    """ Attempts to connect to the database.

        This method attempts a limited number of retries if unable to connect. This
        is intended to support integration tests, which run immediately after the
        local Postgres container is started. In real-world use, we hope to connect
        successfully on the first try.
        """
    for x in range(40):
        try:
            return pg8000.dbapi.connect(**connection_info)
        except:
            time.sleep(0.25)
    raise Exception("timed-out waiting for container to start")
