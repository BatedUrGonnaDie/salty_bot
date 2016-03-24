#! /usr/bin/env python2.7

from modules import irc

class TwitchIRC(irc.IRC):

    def __init__(self, username, oauth):
        super(TwitchIRC, self).__init__("irc.chat.twitch.tv", 6697, True, username, oauth)
        self.total_messages = 0
        self.sent_messages = 0
        self.message_limit = 30

    @property
    def rate_limited(self):
        return self.sent_messages >= self.message_limit

    def privmsg(self, channel, msg):
        if not self.rate_limited:
            super(channel, msg)
            self.sent_messages += 1
            self.total_messages += 1
