#! /usr/bin/env python2.7

import logging
import threading

from modules import twitch_irc
from modules.module_errors import DeactivatedBotException
from modules.module_errors import NewBotException

class Balancer(object):

    def __init__(self):
        self.connections = {}
        self.lock = threading.Semaphore()

    def _create_connection(self, username, oauth):
        # Should only be called while the lock is acquired with fresh data
        # i.e. With the same lock as when you check that there is no connection
        logging.debug("Creating connection for {0}.".format(username))
        t_irc = twitch_irc.TwitchIRC(username, oauth, callback=self.process_incomming)
        t_irc.create()
        t_irc.connect()
        t_irc_thread = threading.Thread(target=t_irc.main_loop)
        t_irc_thread.daemon = True
        self.connections[username] = {"thread" : t_irc_thread, "irc_obj" : t_irc, "bots" : {}}
        t_irc_thread.start()


    def _remove_connection(self, username):
        # Should only be called while the lock is acquired with fresh data
        # i.e. With the same lock as when you check that there is no more bots on a connection
        logging.debug("Removing connection for {0}.".format(username))
        self.connections[username]["irc_obj"].continue_loop = False
        self.connections[username]["thread"].join()
        del self.connections[username]

    def add_bot(self, bot, lock = True):
        # This will overwrite any bot under the exact same name in the same channel
        # Up to implementer to check for conflictions
        # Lock should only be disabled if currently acquired from another source
        logging.debug("Adding bot for {0}.".format(bot.channel))
        if lock:
            self.lock.acquire()
        if not self.connections.get(bot.bot_nick, None):
            self._create_connection(bot.bot_nick, bot.bot_oauth)

        self.connections[bot.bot_nick]["bots"][bot.channel] = bot
        self.connections[bot.bot_nick]["irc_obj"].join(bot.channel)
        if lock:
            self.lock.release()

    def update_bot(self, new_config):
        with self.lock:
            try:
                self.connections["bots"][new_config["twitch_name"]].update_config(new_config)
            except KeyError:
                # Tells the main thread/listener to create a fresh bot
                raise NewBotException
            except DeactivatedBotException:
                self.remove_bot(new_config["bot_name"], new_config["twitch_name"], lock=False)

    def update_twitch(self, new_info):
        with self.lock:
            for v in self.connections.values():
                for k2, v2 in v["bots"].iteritems():
                    v2.update_twitch_info(new_info[k2])

    def remove_bot(self, bot_name, channel_name, lock = True):
        # Lock should only be disabled if currently acquired from another source
        logging.debug("Removing bot for {0}.".format(bot_name))
        if lock:
            self.lock.acquire()
        self.connections[bot_name]["irc_obj"].part(channel_name)
        del self.connections[bot_name]["bots"][channel_name]
        if not self.connections[bot_name].get("bots", None):
            self._remove_connection(bot_name)
        if lock:
            self.lock.release()

    def process_incomming(self, c_msg):
        with self.lock:
            if c_msg["action"] == "RECONNECT":
                irc_obj = self.connections[c_msg["bot_name"]]["irc_obj"]
                old_host = irc_obj.host
                irc_obj.host = irc_obj.get_peer_ip()
                irc_obj.reconnect()
                irc_obj.host = old_host

            bot_obj = self.connections[c_msg["bot_name"]]["bots"][c_msg["channel"][1:]]
        try:
            outbound = bot_obj.process_message(c_msg)
        except Exception, e:
            logging.exception(e)
            return

        if outbound and False:
            with self.lock:
                self.connections[c_msg["bot_name"]]["irc_obj"].privmsg(c_msg["channel"][1:], outbound)
        elif outbound:
            print "[DARK] {0} {1}: {2}".format(c_msg["channel"], c_msg["bot_name"], outbound)
