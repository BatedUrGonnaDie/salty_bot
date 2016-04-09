#! /usr/bin/env python2.7

import threading

from modules import twitch_irc

class Balancer(object):

    def __init__(self):
        self.connections = {}
        self.lock = threading.Semaphore()

    def _create_connection(self, username, oauth):
        # Should only be called while the lock is acquired
        t_irc = twitch_irc.TwitchIRC(username, oauth)
        t_irc.create()
        t_irc.connect()
        t_irc_thread = threading.Thread(target=t_irc.main_loop, args=(self.process_incomming,))
        t_irc_thread.daemon = True
        self.connections[username] = {"thread" : t_irc_thread, "irc_obj" : t_irc, "bots" : {}}
        t_irc_thread.start()

    def _remove_connection(self, username):
        # Should only be called while the lock is acquired
        self.connections[username]["irc_obj"].continue_loop = False
        self.connections[username]["thread"].join()
        del self.connections[username]

    def retrieve_bot_config(self, twitch_name):
        with self.lock:
            return self.connections["bots"][twitch_name].config


    def add_bot(self, bot):
        with self.lock:
            if not self.connections.get(bot.bot_nick, None):
                self._create_connection(bot.bot_nick, bot.bot_oauth)

            self.connections[bot.bot_nick]["bots"][bot.channel] = bot
            self.connections[bot.bot_nick]["irc_obj"].join(bot.channel)

    def update_bot(self, new_config):
        with self.lock:
            self.connections["bots"][new_config["twitch_name"]].update_config(new_config)

    def remove_bot(self, bot_name, channel_name):
        with self.lock:
            self.connections[bot_name]["irc_obj"].part(channel_name)
            del self.connections[bot_name]["bots"][channel_name]
            bots_left = self.connections[bot_name].get("bots", None)
            if not bots_left:
                self._remove_connection(bot_name)

    def process_incomming(self, c_msg):
        with self.lock:
            bot_obj = self.connections[c_msg["bot_name"]]["bots"][c_msg["channel"][1:]]
        outbound = bot_obj.process_message(c_msg)
        if outbound:
            with self.lock:
                self.connections[c_msg["bot_name"]]["irc_obj"].privmsg(c_msg["channel"], outbound)
