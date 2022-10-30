""" Functions that will be called from integration tests. These are in the mainline
    source directory as a convenience.
    """

import os
import pg8000.dbapi as db
import time

from collections import namedtuple

from cf_postgres import util


def local_pg8000_secret(ignored):
    """ Returns connection parameters for the local connection (see Makefile for details).
        This can be called explicitly, or patched over util.retrieve_pg8000_secret()
        """
    return {
        'user':             "postgres",
        'password':         os.environ.get('PGPASSWORD', "postgres"),
        'host':             "localhost",
        'port':             int(os.environ.get('PGPORT', "9432")),
        'database':         "postgres",
        'application_name': "cf-postgres-testing",
    }


def create_user(username):
    """ Creates a user without any privileges/login. Returns the username
        as a convenience.
        """
    with util.connect_to_db(local_pg8000_secret(None)) as conn:
        csr = conn.cursor()
        csr.execute(f"create user {username}")
        conn.commit()
        return username


def retrieve_schema_info(schema_name):
    """ Retrieves basic info about a schema.
        """
    sql = """
          select  s.oid as schema_id,
                  u.usename as owner_name
          from    pg_namespace s
          join    pg_user u on u.usesysid = s.nspowner
          where   s.nspname = %s
          """
    return util.select_as_dict(
                local_pg8000_secret(None),
                lambda c:  c.execute(sql, (schema_name,)))


Permission = namedtuple("Permission", ["permission", "object_type", "is_grantable"], defaults=[None, False])


def _transform_permissions(data):
    """ Transforms the returned data from ACL queries into a dict keyed by grantee,
        with a set of permissions as value. Also translates a null grantee to PUBLIC.
        """
    result = {}
    for row in data:
        grantee = row['grantee'] or "PUBLIC"
        permission = Permission(row['privilege_type'], row.get('object_type'), row['is_grantable'])
        entry = result.get(grantee) or set()
        entry.add(permission)
        result[grantee] = entry
    return result


def retrieve_schema_permissions(schema_name):
    """ Retrieves the explicit permissions granted on a schema, as a dict of
        grantee name to Permission instances.
        """
    sql = """
          with    grants as
                  (
                  select  nspname,
                          (aclexplode(nspacl)).privilege_type as privilege_type,
                          (aclexplode(nspacl)).grantee as grantee_oid,
                          (aclexplode(nspacl)).is_grantable as is_grantable
                  from    pg_namespace
                  )
          select  g.privilege_type,
                  u.usename as grantee,
                  g.is_grantable
          from    grants g
          left join pg_user u
          on      u.usesysid = g.grantee_oid
          where   g.nspname = %s
          """
    return _transform_permissions(util.select_as_dict(
                local_pg8000_secret(None),
                lambda c:  c.execute(sql, (schema_name,))))


def retrieve_default_schema_permissions(schema_name):
    sql = """
          with    grants as
                  (
                  select  s.nspname,
                          d.defaclobjtype as object_type,
                          (aclexplode(d.defaclacl)).privilege_type as privilege_type,
                          (aclexplode(d.defaclacl)).grantee as grantee_oid,
                          (aclexplode(d.defaclacl)).is_grantable as is_grantable
                  from    pg_namespace s
                  join    pg_default_acl d
                  on      d.defaclnamespace = s.oid
                  )
          select  g.object_type,
                  g.privilege_type,
                  u.usename as grantee,
                  g.is_grantable
          from    grants g
          left join pg_user u
          on      u.usesysid = g.grantee_oid
          where   g.nspname = %s
          """
    return _transform_permissions(util.select_as_dict(
                local_pg8000_secret(None),
                lambda c:  c.execute(sql, (schema_name,))))
