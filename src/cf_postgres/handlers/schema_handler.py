""" Handler for User resources.
    """

import logging
import sys

from cf_postgres import util
from cf_postgres.constants import *


# resource configuration

RESOURCE_NAME = "Schema"

PROP_NAME       = "Name"
PROP_OWNER      = "Owner"
PROP_PUBLIC     = "Public"
PROP_READONLY   = "ReadOnly"
PROP_USERS      = "Users"
PROP_ROUSERS    = "ReadOnlyUsers"
PROP_CASCADE    = "Cascade"


def try_handle(conn, request_type, resource_type, physical_id, props, response):
    if resource_type != RESOURCE_NAME:
        return False
    schema_name = util.verify_property(props, response, PROP_NAME)
    if schema_name:
        handle(conn, request_type, physical_id, schema_name, props, response)
    return True


def handle(conn, request_type, physical_id, schema_name, props, response):
    logging.info(f"schema_handler: performing {request_type} for schema {schema_name}, resource {physical_id}")
    owner_name = props.get(PROP_OWNER)
    is_public = util.get_boolean_prop(props, PROP_PUBLIC)
    is_readonly = util.get_boolean_prop(props, PROP_READONLY)
    users = props.get(PROP_USERS, [])
    ro_users = props.get(PROP_ROUSERS, [])
    cascade = util.get_boolean_prop(props, PROP_CASCADE)
    try:
        if request_type == ACTION_CREATE:
            doCreate(conn, schema_name, owner_name, is_public, is_readonly, users, ro_users, response)
        elif request_type == ACTION_UPDATE:
            if physical_id == schema_name:
                doUpdate(conn, schema_name, owner_name, is_public, is_readonly, users, ro_users, response)
            else:
                util.report_failure(response, "Can not update schema name", physical_id)
        elif request_type == ACTION_DELETE:
            doDelete(conn, physical_id, cascade, response)
        else:
            util.report_failure(response, f"schema_handler: Unknown request type: {request_type}")
    except:
        util.report_failure(response, f"schema_handler: failed to complete action {request_type} for schema {schema_name}: {sys.exc_info()[1]}", physical_id)
        conn.rollback()


def doCreate(conn, schema_name, owner_name, is_public, is_readonly, users, ro_users, response):
    csr = conn.cursor()
    if owner_name:
        csr.execute(f"create schema if not exists {schema_name} authorization {owner_name}")
    else:
        csr.execute(f"create schema if not exists {schema_name}")
    if is_public or is_readonly:
        apply_grants(csr, schema_name, "PUBLIC", is_readonly)
    for user in users:
        apply_grants(csr, schema_name, user, False)
    for user in ro_users:
        apply_grants(csr, schema_name, user, True)
    conn.commit()
    util.report_success(response, schema_name)


def doUpdate(conn, schema_name, owner, is_public, is_readonly,users, ro_users, response):
    csr = conn.cursor()
    # TODO
    conn.commit()
    util.report_success(response, schema_name)


def doDelete(conn, schema_name, cascade, response):
    csr = conn.cursor()
    if cascade:
        csr.execute(f"drop schema if exists {schema_name} cascade")
    else:
        csr.execute(f"drop schema if exists {schema_name}")
    conn.commit()
    util.report_success(response, schema_name)


def apply_grants(csr, schema_name, recipient, is_readonly):
    if is_readonly:
        csr.execute(f"grant usage on schema {schema_name} to {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} grant select on tables to {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} grant select, usage on sequences to {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} grant execute on functions to {recipient}")
    else:
        csr.execute(f"grant all on schema {schema_name} to {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} grant all on tables to {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} grant all on sequences to {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} grant all on functions to {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} grant all on types to {recipient}")
