#! /usr/bin/env python2.7

import imp
import logging
import os
import sys
import threading

from modules import twitch_irc
from modules.module_errors import DeactivatedBotException
from modules.module_errors import NewBotException

helper_functions = {
    "PRIVMSG"         : [],
    "NOTICE"          : [],
    "USERSTATE"       : [],
    "GLOBALUSERSTATE" : [],
    "HOSTTARGET"      : [],
    "CLEARCHAT"       : [],
    "JOIN"            : [],
    "PART"            : [],
    "MODE"            : [],
    "RECONNECT"       : [],
    "ROOMSTATE"       : [],
    "CAP"             : []
}

def init_helpers():
    for k in helper_functions.keys():
        helper_functions[k] = []
    helper_filenames = []
    helper_folder = os.path.join(os.path.dirname(__file__), "helpers")

    for fn in os.listdir(helper_folder):
        if os.path.isdir(fn) or not fn.endswith(".py") or fn.startswith("_"):
            continue
        helper_filenames.append(os.path.join(helper_folder, fn))
    for helper in helper_filenames:
        imp_name = os.path.basename(helper)[:-3]
        try:
            module = imp.load_source(imp_name, helper)
            sys.modules[imp_name] = module
            helper_functions[module.ON_ACTION].append(module.call)
        except Exception, e:
            print "Error importing {0}.".format(imp_name)
            print e

init_helpers()

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
        self.connections[username]["irc_obj"].disconnect()
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
                self.connections[new_config["bot_nick"]]["bots"][new_config["twitch_name"]].update_config(new_config)
                logging.debug("Updated bot for {0}.".format(new_config["twitch_name"]))
            except KeyError:
                # Tells the main thread/listener to create a fresh bot
                raise NewBotException
            except DeactivatedBotException:
                self.remove_bot(new_config["bot_nick"], new_config["twitch_name"], lock=False)

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
            bot_obj = self.connections[c_msg["bot_name"]]["bots"][c_msg["channel"][1:]]
        try:
            outbound = bot_obj.process_message(c_msg)
        except Exception, e:
            logging.exception(e)
            logging.error(c_msg)
            return

        if outbound:
            with self.lock:
                self.connections[c_msg["bot_name"]]["irc_obj"].privmsg(c_msg["channel"][1:], outbound)
            print "{0} {1}: {2}".format(c_msg["channel"], c_msg["bot_name"], outbound)

        for k, v in helper_functions.iteritems():
            if k == c_msg["action"]:
                for i in v:
                    try:
                        success, response = i(bot_obj, c_msg, self)
                    except Exception, e:
                        logging.error("Error in callback for {0}s".format(k))
                        logging.exception(e)
                        continue
                    if success and response:
                        self.connections[c_msg["bot_name"]]["irc_obj"].privmsg(c_msg["channel"][1:], response)
                break
