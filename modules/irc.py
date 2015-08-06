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
        self.irc.sendall("{0}\r\n".format(msg))

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

    def recv(self, amount):
        inc_msg = self.irc.recv(amount)
        try:
            return inc_msg.decode("utf-8")
        except Exception, e:
            logging.exception(e)
            return inc_msg

    def tokenize(self, raw_msg):
        raise NotImplementedError
