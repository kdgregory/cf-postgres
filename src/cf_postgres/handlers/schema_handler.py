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


def try_handle(conn, request_type, resource_type, physical_id, props, old_props, response):
    if resource_type != RESOURCE_NAME:
        return False
    schema_name = util.verify_property(props, response, PROP_NAME)
    if schema_name:
        handle(conn, request_type, physical_id, schema_name, props, old_props, response)
    return True


def handle(conn, request_type, physical_id, schema_name, props, old_props, response):
    logging.info(f"schema_handler: performing {request_type} for schema {schema_name}, resource {physical_id}")
    try:
        if request_type == ACTION_CREATE:
            _doCreate(conn, schema_name, props, response)
        elif request_type == ACTION_UPDATE:
            _doUpdate(conn, physical_id, schema_name, props, old_props, response)
        elif request_type == ACTION_DELETE:
            _doDelete(conn, physical_id, props, response)
        else:
            util.report_failure(response, f"schema_handler: Unknown request type: {request_type}")
    except:
        util.report_failure(response, f"schema_handler: failed to complete action {request_type} for schema {schema_name}: {sys.exc_info()[1]}", physical_id)
        conn.rollback()


def _doCreate(conn, schema_name, props, response):
    (owner_name, is_public, is_readonly, users, ro_users) = _extract_props(props)
    csr = conn.cursor()
    if owner_name:
        csr.execute(f"create schema if not exists {schema_name} authorization {owner_name}")
    else:
        csr.execute(f"create schema if not exists {schema_name}")
    if is_public or is_readonly:
        _apply_grants(csr, schema_name, "PUBLIC", is_readonly)
    for user in users:
        _apply_grants(csr, schema_name, user, False)
    for user in ro_users:
        _apply_grants(csr, schema_name, user, True)
    conn.commit()
    util.report_success(response, schema_name)


def _doUpdate(conn, physical_id, schema_name, props, old_props, response):
    (new_owner_name, new_is_public, new_is_readonly, new_users, new_ro_users) = _extract_props(props)
    (old_owner_name, old_is_public, old_is_readonly, old_users, old_ro_users) = _extract_props(old_props)
    schema_name = _opt_rename_schema(conn, physical_id, schema_name)
    csr = conn.cursor()
    if new_owner_name != old_owner_name:
        csr.execute(f"alter schema {schema_name} owner to  {new_owner_name}")
    if old_is_public and not new_is_public:
        _apply_revokes(csr, schema_name, "PUBLIC", old_is_readonly)
        _apply_grants(csr, schema_name, "PUBLIC", new_is_readonly)
    if new_is_public and not old_is_public:
        _apply_revokes(csr, schema_name, "PUBLIC", old_is_readonly)
        _apply_grants(csr, schema_name, "PUBLIC", new_is_readonly)
    for user in old_users:
        if not user in new_users:
            _apply_revokes(csr, schema_name, user, False)
    for user in old_ro_users:
        if not user in new_ro_users:
            _apply_revokes(csr, schema_name, user, True)
    for user in new_ro_users:
        if not user in old_ro_users:
            _apply_grants(csr, schema_name, user, True)
    for user in new_users:
        if not user in old_users:
            _apply_grants(csr, schema_name, user, False)
            
    conn.commit()
    util.report_success(response, schema_name)


def _doDelete(conn, schema_name, props, response):
    cascade = util.get_boolean_prop(props, PROP_CASCADE)
    csr = conn.cursor()
    if cascade:
        csr.execute(f"drop schema if exists {schema_name} cascade")
    else:
        csr.execute(f"drop schema if exists {schema_name}")
    conn.commit()
    util.report_success(response, schema_name)


def _extract_props(props):
    """ Extracts relevant properties as a tuple: (owner, is_public, is_readonly, users, ro_users).
        Can be called for either new or old props.
        """
    return (
        props.get(PROP_OWNER),
        util.get_boolean_prop(props, PROP_PUBLIC),
        util.get_boolean_prop(props, PROP_READONLY),
        props.get(PROP_USERS, []),
        props.get(PROP_ROUSERS, [])
        )
    
def _opt_rename_schema(conn, physical_id, schema_name):
    """ If the provided schema name differs from the existing resource's physical ID,
        renames the schema. Uses a separate transaction to do this (maybe not needed),
        and returns the correct name for further use.
        """
    if physical_id != schema_name:
        csr = conn.cursor()
        csr.execute(f"alter schema {physical_id} rename to  {schema_name}")
        conn.commit()
    return schema_name
    


def _apply_grants(csr, schema_name, recipient, is_readonly):
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


def _apply_revokes(csr, schema_name, recipient, is_readonly):
    if is_readonly:
        csr.execute(f"revoke usage on schema {schema_name} from {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} revoke select on tables from {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} revoke select, usage on sequences from {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} revoke execute on functions from {recipient}")
    else:
        csr.execute(f"revoke all on schema {schema_name} from {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} revoke all on tables from {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} revoke all on sequences from {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} revoke all on functions from {recipient}")
        csr.execute(f"alter default privileges in schema {schema_name} revoke all on types from {recipient}")