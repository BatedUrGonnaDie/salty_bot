#! /usr/bin/env python2.7

import os
import time

command_functions = {
    
}

class SaltyBot(object):

    def __init__(self, config, irc_obj):
        self.config = config
        self.irc = irc_obj

        self.twitch_api = None
        self.osu_api = None
        self.newbs_api = None
        self.srl_api = None
        self.sr_com_api = None
        self.splits_io_api = None
        self.youtube_api = None

        self.message_limit = 30
        self.is_mod = False
        self.rate_limit = 0
        self.messages_received = 0

        self.user_id = config["id"]
        self.session_id = config["session"]

        if self.config["bot_oauth"]:
            self.bot_nick = config["bot_nick"]
            self.bot_oauth = config["bot_oauth"]
        else:
            self.bot_nick = os.environ["default_bot_nick"]
            self.bot_oauth = os.environ["default_bot_oauth"]
        self.channel = config["twtich_name"]

        if config["speedruncom_nick"]:
            self.speedruncom_nick = config["speedruncom_nick"].lower()
        else:
            self.speedruncom_nick = self.channel

        self.game = ""
        self.title = ""
        self.stream_start = ""
        self.is_live = False

        self.blacklist_file = "blacklists/{}_blacklist.txt".format(self.channel)
        with open(self.blacklist_file, "a+") as fin:
            self.blacklist = [x.strip() for x in fin.readlines()]

        self.commands = {}
        self.setup_commands(config)
        self.social = {
            "active": config["social_active"],
            "last_send": time.time(),
            "message_interval": config["social_messages"] or 30,
            "time_interval": config["social_time"] or 10,
            "output": config["social_output"]
        }
        self.toobou = {
            "active": config["toobou_active"],
            "trigger": config["toobou_trigger"],
            "last": 0,
            "limit": config["toobou_limit"] or 30,
            "output": config["toobou_output"]
        }

    def setup_commands(self, config):
        self.commands["!bot_info"] = {
            "custom": False,
            "last": 0,
            "limit": 300,
            "mod_req": False
        }
        self.commands["!help"] = {
            "custom": False,
            "last": 0,
            "limit": 2,
            "mod_req": False
        }
        for i in config["commands"]:
            if i["on"]:
                curr_com = "!{}".format(i["name"])
                self.commands[curr_com] = {
                    "custom": False,
                    "last": 0,
                    "limit": i["limit"] or 30,
                    "mod_req": i["admin"],
                    "function": command_functions[curr_com]
                }
        for i in config["custom_commands"]:
            if i["on"]:
                self.commands["!{}".format(i["name"])] = {
                    "custom": True,
                    "last": 0,
                    "limit": i["limit"] or 30,
                    "mod_req": i["admin"],
                    "output": i["output"]
                }
