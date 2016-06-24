#! /usr/bin/env python2.7

import json
import logging
import os
import socket
import time

import queries

class DBConfig(object):

    def __init__(self, dev, db_url):
        if dev == "development":
            self.dev = True
        else:
            self.dev = False
        self.db_url = db_url

    def initial_retrieve(self):
        with queries.Session(self.db_url) as session:
            if self.dev:
                session.cursor.execute("SELECT * FROM users AS u WHERE u.id=1")
                users = session.cursor.fetchall()
                session.cursor.execute("SELECT * FROM settings AS s WHERE s.user_id=1")
                settings = session.cursor.fetchall()
                session.cursor.execute("SELECT * FROM commands AS c WHERE c.user_id=1")
                commands = session.cursor.fetchall()
                session.cursor.execute("SELECT * FROM custom_commands AS c WHERE c.user_id=1")
                c_commands = session.cursor.fetchall()
            else:
                session.cursor.execute("SELECT * FROM users AS u WHERE u.id IN (SELECT s.user_id FROM settings AS s WHERE s.active=true)")
                users = session.cursor.fetchall()
                session.cursor.execute("SELECT * FROM settings AS s WHERE s.active=true")
                settings = session.cursor.fetchall()
                session.cursor.execute("SELECT * FROM commands AS c WHERE c.user_id IN (SELECT s.user_id FROM settings AS s WHERE s.active=true)")
                commands = session.cursor.fetchall()
                session.cursor.execute("SELECT * FROM custom_commands AS c WHERE c.user_id IN (SELECT s.user_id FROM settings AS s WHERE s.active=true)")
                c_commands = session.cursor.fetchall()

            users_dict = {}
            for i in users:
                user_id = i["id"]
                i["user_id"] = user_id
                users_dict[user_id] = i
                users_dict[user_id]["commands"] = []
                users_dict[user_id]["custom_commands"] = []

            for i in settings:
                users_dict[i["user_id"]]["settings"] = i

            for i in commands:
                users_dict[i["user_id"]]["commands"].append(i)

            for i in c_commands:
                users_dict[i["user_id"]]["custom_commands"].append(i)

        channels_dict = {}
        for v in users_dict.values():
            channels_dict[v["twitch_name"]] = v

        return channels_dict

    def fetch_one(self, user_id):
        pass

class JSONConfig(object):

    def __init__(self, dev, filename):
        self.dev = dev
        self.filename = filename

    def initial_retrieve(self):
        with open(self.filename, "r") as fin:
            configurations = json.load(fin)

        return {k : v for k, v in configurations.iteritems() if v["settings"]["active"]}

    def fetch_one(self, *args):
        return self.initial_retrieve()

class ConfigServer(object):

    def __init__(self, server_type, **kwargs):
        if server_type.upper() == "JSON":
            self.file_name = kwargs["filename"]
            self.last_modified = os.stat(self.file_name).st_mtime
            self.listen_for_updates = self.file_server
        else:
            self.web_ip = kwargs["web_ip"]
            self.web_port = kwargs["web_port"]
            self.web_secret = kwargs["web_secret"]
            self.socket = socket.socket()
            self.socket.bind((self.web_ip, int(self.web_port)))
            self.listen_for_updates = self.db_server

    def file_server(self):
        while True:
            if os.stat(self.file_name).st_mtime != self.last_modified:
                return None
            time.sleep(5)

    def db_server(self):
        while True:
            self.socket.listen(1)
            connection, address = self.socket.accept()
            secret = connection.recv(128)
            if secret != self.web_secret:
                connection.close()
                logging.error("Wrong secret key received from IP: {0}".format(address))
                continue
            to_update = connection.recv(128)
            connection.close()
            return to_update
