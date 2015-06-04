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

    def connect(self):
        self.irc.connect((self.host, self.port))
        self.raw("PASS {}".format(self.oauth))
        self.raw("NICK {}".format(self.username))
        self.connected = True

    def disconnect(self):
        try:
            self.raw("QUIT")
        except Exception:
            pass
        finally:
            self.irc.close()
            self.irc = None
            self.connected = False

    def raw(self, msg):
        self.irc.sendall("{}\r\n".format(msg))

    def join(self, channel):
        self.raw("JOIN #{}".format(channel))

    def part(self, channel):
        self.raw("PART #{}".format(channel))

    def capability(self, cap):
        self.raw("CAP REQ :{}".format(cap))

    def privmsg(self, channel, msg):
        self.raw("PRIVMSG #{} :{}".format(channel, msg))

    def recv(self, amount):
        inc_msg = self.irc.recv(amount)
        try:
            return inc_msg.decode("utf-8")
        except Exception, e:
            logging.exception(e)
            return inc_msg
