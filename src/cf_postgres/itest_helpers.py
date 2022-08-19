""" Functions that will be called from integration tests. These are in the mainline
    source directory as a convenience.
    """

import os
import pg8000.dbapi as db
import time
import unittest


def retrieve_pg8000_secret(ignored):
    """ This is patched over the mainline "util" method with the same name.
        """
    return {
        'user':             "postgres",
        'password':         os.environ.get('PGPASSWORD', "postgres"),
        'host':             "localhost",
        'port':             int(os.environ.get('PGPORT', "5432")),
        'database':         "postgres",
        'application_name': "cf-postgres-testing",
    }


def wait_for_postgres():
    """ We're running integration tests immediately after starting the Postgres container,
        so it's not likely to be ready for us. This method spins, attempting to connect
        every .25 seconds until successful. Times-out after 10 seconds.
        """
    secret = retrieve_pg8000_secret(None)
    for x in range(40):
        try:
            with db.connect(**secret) as cxt:
                return;
        except:
            time.sleep(0.25)
    raise Exception("timed-out waiting for container to start")
