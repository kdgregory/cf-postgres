""" Functions that will be called from integration tests. These are in the mainline
    source directory as a convenience.
    """

import os
import pg8000.dbapi as db
import time
import unittest


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
