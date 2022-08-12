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
        response['Status'] = "FAILED"
        response['Reason'] = f"Missing property \"{name}\""
        return None


@lru_cache(maxsize=1)
def retrieve_secret(secret_arn):
    """ Retrieves the named secret and parses its contents as JSON.
        """
    LOGGER.debug(f"retrieving secret: {secret_arn}")
    try:
        sm_client = boto3.client('secretsmanager')
        secret_json = sm_client.get_secret_value(SecretId=secret_arn)['SecretString']
        return json.loads(secret_json)
    except:
        LOGGER.error("failed to retrieve secret", exc_info=True)


def db_url(secret):
    """ Constructs a database connection URL from the provided dict (assumes fields
        as defined by AWS::SecretsManager::SecretTargetAttachment).
        """
    return f"postgresql+pg8000://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}/{secret['dbname']}"
