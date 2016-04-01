#! /usr/bin/env python2.7

import logging
import socket
import ssl

class IRC(object):

    def __init__(self, host, port, username, oauth = "", use_ssl = False):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.username = username
        self.oauth = oauth
        self.socket = None
        self.timeout_count = 0
        self.connected = False
        self.channels = set()
        self.capabilities = set()
        self.continue_loop = True

    def create(self):
        self.socket = socket.socket()
        self.socket.settimeout(600)
        if self.use_ssl:
            self.socket = ssl.wrap_socket(self.socket)

    def connect(self, callback = None):
        self.socket.connect((self.host, self.port))
        if self.oauth:
            self.raw("PASS {0}".format(self.oauth))
        self.raw("NICK {0}".format(self.username))
        self.connected = True
        if self.channels:
            for i in self.channels:
                self.join(i)
        if callback:
            self.main_loop(callback)

    def disconnect(self):
        try:
            self.raw("QUIT")
        except Exception:
            pass
        finally:
            self.socket.close()
            self.socket = None
            self.connected = False

    def reconnect(self):
        self.disconnect()
        self.connect()

    def raw(self, msg):
        self.socket.sendall("{0}\r\n".format(msg))

    def ping(self):
        self.raw("PING")

    def pong(self, host):
        self.raw("PONG {0}".format(host))

    def join(self, channel):
        self.raw("JOIN #{0}".format(channel))
        self.channels.add(channel)

    def part(self, channel):
        self.raw("PART #{0}".format(channel))
        self.channels.remove(channel)

    def capability(self, cap):
        self.raw("CAP REQ :{0}".format(cap))

    def privmsg(self, channel, msg):
        self.raw("PRIVMSG #{0} :{1}".format(channel, msg))

    def pm(self, user, msg):
        self.raw("PRIVMSG {0} :{1}".format(user, msg))

    def get_peer_ip(self):
        return self.socket.getpeername()[0]

    def recv(self, amount):
        inc_msg = self.socket.recv(amount)
        try:
            return inc_msg.decode("utf-8")
        except Exception, e:
            logging.exception(e)
            return inc_msg

    @staticmethod
    def tokenize(raw_msg):
        c_msg = {}
        msg_split = raw_msg.split(" ")
        if raw_msg.startswith(":"):
            msg_split.insert(0, "")
        if msg_split[0]:
            c_msg["tags"] = IRC.process_tags(msg_split[0])
        else:
            c_msg["tags"] = {}
        c_msg["sender"] = msg_split[1][1:].split("!")[0]
        c_msg["action"] = msg_split[2]
        c_msg["channel"] = msg_split[3]
        try:
            c_msg["message"] = " ".join(msg_split[4:])
            if c_msg["action"] != "CAP":
                c_msg["message"] = c_msg["message"][1:]
        except IndexError:
            c_msg["message"] = ""
        return c_msg

    @staticmethod
    def process_tags(tags):
        tags_dict = dict(item.split("=") for item in tags[0][1:].split(";"))
        for k, v in tags_dict.iteritems():
            k.replace("\\:", ";")
            k.replace("\\s", " ")
            k.replace("\\\\", "\\")
            v.replace("\\:", ";")
            v.replace("\\s", " ")
            v.replace("\\\\", "\\")
        return tags_dict


    def main_loop(self, callback):
        self.socket.settimeout(10)
        msg_buffer = ""
        lines = []
        while self.continue_loop:
            try:
                msg_buffer += self.recv(4096)
            except socket.timeout:
                if self.timeout_count < 60:
                    self.timeout_count += 1
                    continue
                else:
                    self.reconnect()
                    continue
            if msg_buffer == "":
                self.reconnect()
                continue
            lines += msg_buffer.split("\r\n")
            while len(lines) > 1:
                current_message = lines.pop(0)
                if current_message.startswith("PING"):
                    self.pong(current_message.split("PING ")[0])
                    continue

                msg_parts = self.tokenize(current_message)
                msg_parts["bot_name"] = self.username
                if msg_parts["action"] == "CAP":
                    if msg_parts["message"].split(" ")[0] == "ACK":
                        self.capabilities.add(msg_parts["message"].split(" ", 1)[1])
                    else:
                        self.capabilities.remove(msg_parts["message"].split(" ", 1)[1])
                else:
                    callback(msg_parts)
            msg_buffer = lines[0]
