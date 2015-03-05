#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-

import socket
import urlparse

import psycopg2
import psycopg2.extras

class WebRetrieve:

    def __init__(self, db_url, web_port):
        self.db_url = db_url
        self.web_secret = ""
        self.web_port = web_port
        self.web_host = socket.gethostbyname(socket.gethostname())
        self.web_s = socket.socket()
        self.web_s.bind((self.web_host, 6666))
        self.disect_url()

    def disect_url(self):
        urlparse.uses_netloc.append("postgres")
        url_parts = urlparse.urlparse(self.db_url)
        self.db_name = url_parts.path[1:]
        self.db_user = url_parts.username
        self.db_password = url_parts.password
        self.db_host = url_parts.hostname
        self.db_port = url_parts.port

    def db_connect(self):
        conn = psycopg2.connect(database=self.db_name, user=self.db_user, host=self.db_host, password=self.db_password, port=self.db_port)
        return conn

    def db_close(self, connection):
        connection.close()

    def setup_cursor(self, connection_inst, cf_type = psycopg2.extras.RealDictCursor):
        cursor = connection_inst.cursor(cursor_factory=cf_type)
        return cursor

    def close_cursor(self, cursor):
        cursor.close()

    def execute_one(self, cursor, query, parameters = None):
        cursor.execute(query, parameters)
        return cursor.fetchone()

    def execute_all(self, cursor, query, parameters = None):
        cursor.execute(query, parameters)
        return cursor.fetchall()

    def initial_retrieve(self):
        channels_dict = {}

        conn = self.db_connect()
        cur = self.setup_cursor(conn)

        users = self.execute_all(cur, """SELECT * FROM users AS u JOIN settings AS s on u.id=s.user_id WHERE s.active=true""")
        commands = self.execute_all(cur, """SELECT * FROM commands AS c WHERE c.user_id in (SELECT s.user_id FROM Settings AS s WHERE s.active=true)""")
        custom_commands = self.execute_all(cur, """SELECT * FROM custom_commands AS c WHERE c.user_id in (SELECT s.user_id FROM Settings AS s WHERE s.active=true)""")

        self.close_cursor(cur)
        self.db_close(conn)

        users_dict = {}
        for i in users:
            users_dict[i["id"]] = i
            users_dict[i["id"]]["commands"] = []
            users_dict[i["id"]]["custom_commands"] = []

        for i in commands:
            users_dict[i["user_id"]]["commands"].append(i)

        for i in custom_commands:
            users_dict[i["user_id"]]["custom_commands"].append(i)
        for k, v in users_dict.iteritems():
            channels_dict[v["twitch_name"]] = v

        return channels_dict

    def update_retrieve(self, user_id):
        user_dict = {}
        conn = self.db_connect()
        cur = self.setup_cursor(conn)

        user = self.execute_one(cur, """SELECT u.*, s.* FROM users AS u JOIN settings AS s on s.user_id=%s WHERE u.id=%s""", parameters=(user_id, user_id))
        commands = self.execute_all(cur, """SELECT c.* FROM commands AS c WHERE c.user_id=%s""", parameters=(user_id,))
        custom_commands = self.execute_all(cur, """SELECT cc.* FROM custom_commands AS cc WHERE cc.user_id=%s""", parameters=(user_id,))

        name = user["twitch_name"]
        user_dict[name] = user
        user_dict[name]["commands"] = commands
        user_dict[name]["custom_commands"] = custom_commands
        return user_dict

    def main_listen(self):
        self.web_s.listen(1)
        connection, address = self.web_s.accept()
        secret = self.web_s.recv(1024)
        if secret != self.web_secret:
            connection.close()
            raise ValueError
        else:
            to_update = self.web_s.recv(4096)
            connection.close()
            return to_update
