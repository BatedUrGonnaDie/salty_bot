#! /usr/bin/env python2.7

import os
import json
import psycopg2 as pg
import psycopg2.extras as pge
import urlparse
from datetime import datetime

class Database(object):
    """docstring for Database"""
    DB = None
    class Table:
        def __init__(self):
            self.lookup_tables = {}

        def append(self, x):
            self.lookup_tables[x.__name__] = x

        def __getattr__(self, name):
            try:
                return self.lookup_tables[name](Database._make_cursor())

            except KeyError:
                raise AttributeError("name '"+name+"' is not in table")

    tables = Table()

    def __init__(self, URL):
        super(Database, self).__init__()
        
    @classmethod
    def is_connected(Database):
        return not Database.DB.closed

    @classmethod
    def connect_to(Database, URL):
        if not Database.IsConnected():
            try:
                DB_URL = urlparse.urlparse(URL)

                Database.DB = pg.connect(
                    database =  DB_URL.path,
                    user     =  DB_URL.username,
                    password =  DB_URL.password,
                    host     =  DB_URL.hostname,
                    port     =  DB_URL.port
                )

            except pg.OperationalError:
                print "[ERROR] Either there is no url or the database url failed to parse correctally"
    @classmethod
    def disconnect(Database):
        Database.DB.close()

    @classmethod
    def commit_changes(Database):
        if Database.IsConnected():
            Database.DB.commit()

    @classmethod
    def rollback_changes(Database):
        if Database.IsConnected():
            Database.DB.cancel()
            Database.DB.rollback()

    @classmethod
    def _make_cursor(Database):
        return Database.DB.cursor(cursor_factory=pge.RealDictCursor)


    @classmethod
    def attach(Database, table):
        Database.tables.append(table)
        return table




class Query(object):
    """docstring for query"""
    def __init__(self, cursor):
        super(query, self).__init__()
        self.cursor = cursor
        self.query = None

    def __call__(self, query = None):
        if query is not None:
            self.query = query

        if self.query is None:
            raise ValueError("No specified query")

    def __iter__(self):
        pass

    def __execute(self):
        self.cursor.execute(self.query)

    
@Database.attach    
class Users(Query):
    base_query = """SELECT * FROM users """

    def user_data(self, user):
        self.query = self.base_query+"WHERE twitch_name ="+user
        
    def user_id(self, user):
Database.tables.Query
