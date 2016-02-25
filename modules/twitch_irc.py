#! /usr/bin/env python2.7

import socket

from modules import irc

class TwitchIRC(irc.IRC):

    def __init__(self, host, port, username, oauth):
        super(TwitchIRC, self).__init__(host, port, username, oauth)
        self.sent_messages = 0
        self.message_limit = 30

    @property
    def rate_limited(self):
        return self.sent_messages >= self.message_limit

    def privmsg(self, channel, msg):
        if not self.rate_limited:
            super(channel, msg)

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
                callback(msg_parts)
            msg_buffer = lines[0]

    def tokenize(self, raw_msg):
        c_msg = {}
        msg_split = raw_msg.split(" ")
        if raw_msg.startswith(":"):
            msg_split.insert(0, "")
        if msg_split[0]:
            c_msg["tags"] = dict(item.split("=") for item in msg_split[0][1:].split(";"))
        else:
            c_msg["tags"] = {}
        c_msg["sender"] = msg_split[1][1:].split("!")[0]
        c_msg["action"] = msg_split[2]
        c_msg["channel"] = msg_split[3]
        try:
            c_msg["message"] = " ".join(msg_split[4:])[1:]
        except IndexError:
            c_msg["message"] = ""
        return c_msg
