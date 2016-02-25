#! /usr/bin/env python2.7

import logging
import socket

class IRC(object):

    def __init__(self, host, port, username, oauth = ""):
        self.host = host
        self.port = port
        self.username = username
        self.oauth = oauth
        self.socket = None
        self.connected = False

    def create(self):
        self.socket = socket.socket()
        self.socket.settimeout(600)

    def connect(self, callback = None):
        self.socket.connect((self.host, self.port))
        if self.oauth:
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
            self.socket.close()
            self.socket = None
            self.connected = False

    def reconnect(self, callback):
        self.disconnect()
        self.connect(callback)

    def raw(self, msg):
        self.socket.sendall("{0}\r\n".format(msg))

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
        return self.socket.getpeername()[0]

    def recv(self, amount):
        inc_msg = self.socket.recv(amount)
        try:
            return inc_msg.decode("utf-8")
        except Exception, e:
            logging.exception(e)
            return inc_msg

    def tokenize(self, raw_msg):
        raise NotImplementedError

    def main_loop(self, callback):
        raise NotImplementedError
