""" Integration tests for the CreateUser action: creates and verifies a user in a
    local database. ** Does not clean up afterward **
    """

import copy
import json
import random
import unittest
from unittest.mock import Mock, patch, ANY

import pg8000.dbapi

from cf_postgres import util
from cf_postgres.handlers import user as user_handler
from cf_postgres.itest_helpers import local_pg8000_secret


class TestUserHandler(unittest.TestCase):

    def setUp(self):
        randval = random.randrange(100000, 999999)
        self.username = f"user_{randval}"
        self.password = f"pass_{randval}"
        self.response = {}


    def retrieve_user_info(self):
        # running from a separate connection ensures that we commit our transactions
        with util.connect_to_db(local_pg8000_secret(None)) as conn:
            csr = conn.cursor()
            csr.execute("select * from pg_user where usename = %s", (self.username,))
            return csr.fetchall() 


    def assert_user_can_login(self):
        # verify that we properly supplied the password
        connection_info = copy.deepcopy(local_pg8000_secret(None))
        connection_info['user'] = self.username
        connection_info['password'] = self.password
        with pg8000.dbapi.connect(**connection_info) as conn:
            pass # success! (failure will throw)


    def test_create_from_username_and_password(self):
        props = {
                    "Username":     self.username,
                    "Password":     self.password,
                }
        with util.connect_to_db(local_pg8000_secret(None)) as conn:
            result = user_handler.try_handle("CreateUser", "Create", conn, props, self.response)
        self.assertTrue(result)
        self.assertEqual(self.response,
                          {
                            "Status": "SUCCESS",
                            "PhysicalResourceId": self.username,
                          })
        self.assertEqual(len(self.retrieve_user_info()), 1)
        self.assert_user_can_login()


    def test_create_from_username(self):
        props = {
                    "Username":     self.username,
                }
        with util.connect_to_db(local_pg8000_secret(None)) as conn:
            result = user_handler.try_handle("CreateUser", "Create", conn, props, self.response)
        self.assertTrue(result)
        self.assertEqual(self.response,
                          {
                            "Status": "SUCCESS",
                            "PhysicalResourceId": self.username,
                          })
        self.assertEqual(len(self.retrieve_user_info()), 1)


    def test_delete(self):
        props = {
                    "Username":     self.username,
                }
        with util.connect_to_db(local_pg8000_secret(None)) as conn:
            csr = conn.cursor()
            csr.execute(f"create user {self.username} password NULL")
            conn.commit()
        self.assertEqual(len(self.retrieve_user_info()), 1) # test the test
        with util.connect_to_db(local_pg8000_secret(None)) as conn:
            result = user_handler.try_handle("CreateUser", "Delete", conn, props, self.response)
        self.assertEqual(self.response,
                          {
                            "Status": "SUCCESS",
                            "PhysicalResourceId": self.username,
                          })
        self.assertEqual(len(self.retrieve_user_info()), 0)
