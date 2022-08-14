## this is a test that verifies we can connect to the database
## it will be removed once there's a real integration test

import unittest

from cf_postgres.itest_helpers import wait_for_postgres


class TestLambdaHandler(unittest.TestCase):

    def test_connection(self):
        wait_for_postgres()
        # success!
