#! /usr/bin/env python2.7

import logging
import socket

class IRC(object):

    def __init__(self, host, port, username, oauth):
        self.host = host
        self.port = port
        self.username = username
        self.oauth = oauth
        self.irc = None
        self.connected = False

    def create(self):
        self.irc = socket.socket()
        self.irc.settimeout(600)

    def connect(self, callback = None):
        self.irc.connect((self.host, self.port))
        self.raw("PASS {}".format(self.oauth))
        self.raw("NICK {}".format(self.username))
        self.connected = True
        if callback:
            self.main_loop(callback)

    def disconnect(self):
        try:
            self.raw("QUIT")
        except Exception:
            pass
        finally:
            self.irc.close()
            self.irc = None
            self.connected = False

    def reconnect(self, callback):
        self.disconnect()
        self.connect(callback)

    def raw(self, msg):
        self.irc.sendall("{0}\r\n".format(msg))

    def ping(self):
        self.raw("PING")

    def pong(self, host):
        self.raw("PONG {0}".format(host))

    def join(self, channel):
        self.raw("JOIN #{0}".format(channel))

    def part(self, channel):
        self.raw("PART #{0}".format(channel))

    def capability(self, cap):
        self.raw("CAP REQ :{0}".format(cap))

    def privmsg(self, channel, msg):
        self.raw("PRIVMSG #{0} :{1}".format(channel, msg))

    def pm(self, user, msg):
        self.raw("PRIVMSG {0} :{1}".format(user, msg))

    def get_peer_ip(self):
        return self.irc.getpeername()[0]

    def recv(self, amount):
        inc_msg = self.irc.recv(amount)
        try:
            return inc_msg.decode("utf-8")
        except Exception, e:
            logging.exception(e)
            return inc_msg

    def main_loop(self, callback):
        msg_buffer = ""
        lines = []
        while self.connected:
            try:
                msg_buffer += self.recv(4096)
            except socket.timeout:
                self.reconnect(callback)
                continue
            if msg_buffer == "":
                self.reconnect(callback)
                continue
            lines += msg_buffer.split("\r\n")
            while len(lines) > 1:
                current_message = lines.pop(0)
                if current_message.startswith("PING"):
                    self.pong(current_message.split("PING ")[0])
                    continue

                msg_parts = self.tokenize(current_message)
                callback(tags=msg_parts["tags"],
                         sender=msg_parts["sender"],
                         action=msg_parts["action"],
                         channel=msg_parts["channel"],
                         message=msg_parts["message"])
            msg_buffer = lines[0]

    def tokenize(self, raw_msg):
        c_msg = {}
        msg_split = raw_msg.split(" ")
        if raw_msg.startswith(":"):
            msg_split.insert(0, "")
        if msg_split[0]:
            c_msg["tags"] = dict(item.split("=") for item in msg_split[0][1:].split(";"))
        else:
            # Dict of None so that stinn of dict type
            c_msg["tags"] = {}
        c_msg["sender"] = msg_split[1][1:].split("!")[0]
        c_msg["action"] = msg_split[2]
        c_msg["channel"] = msg_split[3]
        try:
            c_msg["message"] = " ".join(msg_split[4:])[1:]
        except IndexError:
            # Blank string over None so that it is still of string type
            c_msg["message"] = ""
        return c_msg
