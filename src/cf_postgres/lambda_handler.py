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
import os
import sys
import uuid

import pg8000.dbapi
import requests

from cf_postgres import util
from cf_postgres.constants import *
from cf_postgres.handlers import test_handler, user_handler


log_level = os.environ.get("LOG_LEVEL", logging.INFO)
logging.getLogger().setLevel(log_level)


HANDLERS = [
    test_handler, 
    user_handler, 
    ]


def handle(event, context):
    # print(json.dumps(event), file=sys.stderr)   # useful for debugging
    response_url = event[REQ_RESPONSE_URL]
    response = {
        RSP_REQUEST_ID:     event[REQ_REQUEST_ID],
        RSP_STACK_ID:       event[REQ_STACK_ID],
        RSP_LOGICAL_ID:     event[REQ_LOGICAL_ID],
        RSP_PHYSICAL_ID:    "to_be_populated",              # required, even for failure
    }
    try:
        request_type = event.get(REQ_REQUEST_TYPE)
        physical_id = event.get(REQ_PHYSICAL_ID)
        props = event.get(REQ_PROPERTIES, {})
        old_props = event.get(REQ_OLD_PROPERTIES, {})
        resource_type = util.verify_property(props, response, REQ_RESOURCE_TYPE)
        secret_arn = util.verify_property(props, response, REQ_ADMIN_SECRET)
        print("resource_type = {resource_type}")
        print("secret_arn = {secret_arn}")
        if resource_type and secret_arn:
            with open_connection(secret_arn) as conn:
                try_handlers(conn, request_type, resource_type, physical_id, props, old_props, response)
    except Exception as ex:
        util.report_failure(response, f"Unhandled exception: \"{ex}\"")
        logging.error("unhandled exception", exc_info=True)
    send_response(response_url, response)


def open_connection(secret_arn):
    """ Establishes the connection to the database. Any exceptions are allowed
        to propagate.
        """
    connection_info = util.retrieve_pg8000_secret(secret_arn)
    logging.info(f"connecting to {connection_info.get('host')}:{connection_info.get('port')}, "
                f"database {connection_info.get('database')} as user {connection_info.get('user')}")
    return pg8000.dbapi.connect(**connection_info)


def try_handlers(conn, request_type, resource_type, physical_id, props, old_props, response):
    """ Runs through the list of handlers, returning once one handles the resource.
        Fails the invocation if there aren't any handlers.
        """
    for handler in HANDLERS:
        if handler.try_handle(conn, request_type, resource_type, physical_id, props, old_props, response):
            return
    util.report_failure(response, f"Unknown resource: \"{resource_type}\"")


def send_response(response_url, response):
    logging.info(f"sending response to {response_url}: {response}")
    rsp = requests.put(response_url, data=json.dumps(response))
    logging.info(f"response status code: {rsp.status_code}")
