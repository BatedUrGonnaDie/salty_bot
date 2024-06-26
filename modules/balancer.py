#! /usr/bin/env python3.7

import imp
import logging
import os
import sys
import threading
import time
from typing import Any, Callable, Dict, List

from modules import twitch_irc
from modules.saltybot import SaltyBot
from modules.module_errors import DeactivatedBotException
from modules.module_errors import NewBotException

helper_functions: Dict[str, List[Callable]] = {
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
    "CAP"             : [],
    "USERNOTICE"      : []
}


def init_helpers() -> None:
    for k in list(helper_functions.keys()):
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
            # mypy cannot infer module properties when dynamically loading apparently
            helper_functions[module.ON_ACTION].append(module.call)  # type: ignore
        except Exception as e:
            print("Error importing {0}.".format(imp_name))
            print(e)


init_helpers()


class Balancer:

    def __init__(self) -> None:
        self.connections: Dict[str, Any] = {}
        self.bot_lookup = {}
        self.social_thread = threading.Thread(target=self.social_message_send)
        self.social_thread.daemon = True
        self.social_thread.start()
        self.lock = threading.Semaphore()

    def _create_connection(self, username: str, oauth: str) -> None:
        # Should only be called while the lock is acquired with fresh data
        # i.e. With the same lock as when you check that there is no connection
        logging.info("Creating connection for {0}.".format(username))
        t_irc = twitch_irc.TwitchIRC(username, oauth, callback=self.process_incomming)
        t_irc.connect()
        t_irc_thread = threading.Thread(target=t_irc.main_loop)
        t_irc_thread.daemon = True
        self.connections[username] = {"thread": t_irc_thread, "irc_obj": t_irc, "bots": {}}
        t_irc_thread.start()

    def _remove_connection(self, username: str) -> None:
        # Should only be called while the lock is acquired with fresh data
        # i.e. With the same lock as when you check that there is no more bots on a connection
        logging.info("Removing connection for {0}.".format(username))
        self.connections[username]["irc_obj"].continue_loop = False
        self.connections[username]["irc_obj"].disconnect()
        del self.connections[username]

    def add_bot(self, bot: SaltyBot, lock=True) -> None:
        # This will overwrite any bot under the exact same name in the same channel
        # Up to implementer to check for conflictions
        # Lock should only be disabled if currently acquired from another source
        logging.info("Adding bot for {0}.".format(bot.channel))
        if lock:
            self.lock.acquire()
        if not self.connections.get(bot.bot_nick, None):
            self._create_connection(bot.bot_nick, bot.bot_oauth)

        self.connections[bot.bot_nick]["bots"][bot.channel] = bot
        self.connections[bot.bot_nick]["irc_obj"].join(bot.channel)
        self.bot_lookup[bot.channel] = bot.twitch_id
        if lock:
            self.lock.release()

    def update_bot(self, new_config: Dict[str, Any]) -> None:
        with self.lock:
            try:
                self.connections[new_config["bot_nick"]]["bots"][new_config["twitch_name"]].update_config(new_config)
                logging.info("Updated bot for {0}.".format(new_config["twitch_name"]))
            except KeyError:
                # Tells the main thread/listener to create a fresh bot
                # First it checks to make sure a bot under a different name isn't still in the channel
                channel = new_config["twitch_name"]
                bot_name = None
                for k, v in self.connections.items():
                    if channel in list(v["bots"].keys()):
                        bot_name = k
                if bot_name:
                    self.remove_bot(bot_name, channel, lock=False)
                raise NewBotException
            except DeactivatedBotException:
                self.remove_bot(new_config["bot_nick"], new_config["twitch_name"], lock=False)

    def update_twitch(self, new_info: Dict[str, Any]) -> None:
        with self.lock:
            for v in list(self.connections.values()):
                for k2, v2 in v["bots"].items():
                    v2.update_twitch_info(new_info[k2])

    def remove_bot(self, bot_name: str, channel_name: str, lock=True) -> None:
        # Lock should only be disabled if currently acquired from another source
        logging.info("Removing bot for {0}.".format(channel_name))
        if lock:
            self.lock.acquire()
        self.connections[bot_name]["irc_obj"].part(channel_name)
        del self.connections[bot_name]["bots"][channel_name]
        del self.bot_lookup[bot_name]
        if not self.connections[bot_name]["bots"]:
            self._remove_connection(bot_name)
        if lock:
            self.lock.release()

    def shutdown(self):
        with self.lock:
            for k, v in self.connections.items():
                v["irc_obj"].disconnect()

    def social_message_send(self) -> None:
        while True:
            for value in list(self.connections.values()):
                for bot in list(value["bots"].values()):
                    if not bot.social["active"]:
                        continue
                    cur_time = time.time()
                    if cur_time < bot.social["time_interval"] + bot.social["last_send"]:
                        continue
                    cur_messages = bot.messages_received
                    if cur_messages < bot.social["message_interval"] + bot.social["last_message"]:
                        continue

                    msg = bot.social["output"]
                    value["irc_obj"].privmsg(bot.channel, msg)
                    bot.social["last_send"] = cur_time
                    bot.social["last_message"] = cur_messages
            time.sleep(15)

    def process_incomming(self, c_msg: Dict[str, Any]) -> None:
        outbound = []
        with self.lock:
            bots = self.connections[c_msg["bot_name"]]["bots"]
            if c_msg.get("channel", None):
                bots = [bots[c_msg["channel"][1:]]]
            else:
                bots = list(bots.values())

        for i in bots:
            try:
                outbound_msg = i.process_message(c_msg)
                if outbound_msg:
                    outbound.append({"channel": i.channel, "message": outbound_msg})
            except Exception as e:
                logging.exception(e)
                logging.error(c_msg)
                return

        if outbound:
            with self.lock:
                for i in outbound:
                    self.connections[c_msg["bot_name"]]["irc_obj"].privmsg(i["channel"], i["message"])

        self.process_helpers(c_msg)

    def process_helpers(self, c_msg: Dict[str, Any]) -> None:
        channel = c_msg.get("channel", None)
        if channel:
            with self.lock:
                channel = channel[1:]
                bot_obj = self.connections[c_msg["bot_name"]]["bots"][channel]
        else:
            bot_obj = None

        for i in helper_functions[c_msg["action"]]:
            try:
                success, response = i(bot_obj, c_msg, self)
            except Exception as e:
                logging.exception(e)
                continue
            if success and response and channel:
                with self.lock:
                    self.connections[c_msg["bot_name"]]["irc_obj"].privmsg(channel, response)
