#! /usr/bin/env python2.7

import os
import json
import psycopg2 as pg
import psycopg2.extras as pge
import urlparse
from datetime import datetime
import time
class Database(object):
    """docstring for Database"""
    DB = None
    class Table:
        def __init__(self):
            self.lookup_tables = {}
            self.cached_objects = {}

        def append(self, x):
            self.lookup_tables[x.__name__] = x

        def __getattr__(self, name):
            requested_table = None
            #Main goal: Return CACHED object
            try:
                #Return if exists
                requested_table = self.cached_objects[name]

            except KeyError:
                if name not in self.lookup_tables:
                    raise AttributeError("Class '"+name+"' does not exist or has not been registered")

                requested_table = self.cached_objects[name] = self.lookup_tables[name](Database._make_cursor())

            finally:
                return requested_table


    tables = Table()

    def __init__(self, URL):
        super(Database, self).__init__()
        
    @classmethod
    def is_connected(Database):
        try:
            return not Database.DB.closed
        except AttributeError:
            print "Database has not been initialized : Not connected"
            return False

    @classmethod
    def connect_to(Database, URL):

        if not Database.is_connected():
            try:
                DB_URL = urlparse.urlparse(URL)
                
                Database.DB = pg.connect(
                    database =  DB_URL.path[1:],
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
    """docstring for Query"""
    def __init__(self, cursor):
        super(Query, self).__init__()
        self.cursor = cursor
        self.query = None

    def __call__(self): 
        if self.query is None:
            raise ValueError("No specified query")

        self._execute()

        return self

    def __iter__(self):
        return self.cursor

    def __str__(self):
        tmp = self.cursor.fetchall()
        if len(tmp) == 1:
            return str(tmp[0])
        elif len(tmp) > 1:
            return tmp

        else:
            return None

    def _execute(self):
        self.cursor.execute(self.query)

    def _close(self):
        self.cursor.close()

    
@Database.attach    
class Users(Query):
    """docstring for Users table"""
    base_query = """SELECT {interest} FROM users """
    def __call__(self):
        self.query = self.base_query.format(interest='*')
        return super(Users, self).__call__()

    
    def user_data(self, user):
        self.query = self.base_query.format(interest='*')+"WHERE twitch_name='"+user+"'"
        self._execute()
        return self
        
    def user_id(self, username):
        self.query = self.base_query.format(interest="id")+"WHERE twitch_name='"+user+"'"

    def user_username(self, id):
        self.query = self.base_query.format(interest="twitch_name")+"WHERE id='"+str(id)+"'"
        self._execute()
        return self

@Database.attach
class Settings(Query):
    """docstring for Settings table"""
    def __call__(self):
        self.query = "SELECT * FROM settings"
        return super(Settings, self).__call__()

@Database.attach
class Commands(Query):
    """docstring for Commands table"""
    def __call__(self):
        self.query = "SELECT * FROM commands"
        return super(Commands, self).__call__()

@Database.attach
class CustomCommands(Query):
    """docstring for CustomCommands table"""
    def __call__(self):
        self.query = "SELECT * FROM custom_commands"
        return super(CustomCommands, self).__call__()
        
@Database.attach
class Textutils(Query):
    """docstring for Textutils table"""
    def __call__(self):
        self.query = "SELECT * FROM textutils"
        return super(Textutils, self).__call__()

if __name__=="__main__":
    def print_me(table_iterator):
        assert(issubclass(table_iterator.__class__, Query))

        for row in table_iterator():
            for k,v in row.items():
                if k == "user_id":
                    try:
                        print k,v,
                        print Database.tables.Users.user_username(v)
                    except:
                        print None

                else:
                    print k,v
            print

    def write_me(table_iterator):
        assert(issubclass(table_iterator.__class__, Query))
        with open(table_iterator.__class__.__name__+".out.txt",'w') as fout:

            for row in table_iterator():
                for k,v in row.items():
                    out = str(k)+' : '+str(v)

                    if k == "user_id":
                        try:
                            fout.write(out)
                            fout.write(Database.tables.Users.user_username(v))
                        except:
                            pass

                    else:
                        fout.write(out)
                
    try:

        Database.connect_to("REDACTED POSTGRES URL")
        write_me(Database.tables.Textutils)
                   
    finally:
        Database.disconnect()

    
