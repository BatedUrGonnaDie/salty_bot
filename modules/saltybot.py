#! /usr/bin/env python2.7

import imp
import os
import sys
import time

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')))

command_functions = {}

def init_commands():
    cmd_filenames = []
    cmd_folder = os.path.join(os.getcwd(), "commands")
    for fn in os.listdir(cmd_folder):
        if os.path.isdir(fn) or not fn.endswith(".py") or fn.startswith("_"):
            continue
        cmd_filenames.append(os.path.join(cmd_folder, fn))
    for cmd in cmd_filenames:
        imp_name = os.path.basename(cmd)[:-3]
        cmd_name = "!{0}".format(imp_name)
        try:
            module = imp.load_source(imp_name, cmd)
            sys.modules[imp_name] = module
            command_functions[cmd_name] = module.call
        except Exception, e:
            print "Error importing {0}.".format(imp_name)
            print e

init_commands()

class SaltyBot(object):

    def __init__(self, config, apis):
        self.action_functions = {
            "PRIVMSG"         : self.privmsg,
            "NOTICE"          : self.notice,
            "USERSTATE"       : self.userstate,
            "GLOBALUSERSTATE" : self.globaluserstate,
            "HOSTTARGET"      : self.hosttarget,
            "CLEARCHAT"       : self.clearchat,
            "JOIN"            : self.join,
            "PART"            : self.part,
            "MODE"            : self.mode,
            "RECONNECT"       : self.reconnect,
            "ROOMSTATE"       : self.roomstate
        }

        self.config = config

        self.twitch_api = apis["twitch"]
        self.osu_api = apis["osu"]
        self.newbs_api = apis["newbs"]
        self.srl_api = apis["srl"]
        self.sr_com_api = apis["sr_com"]
        self.splits_io_api = apis["splits_io"]
        self.youtube_api = apis["youtube"]

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
        self.game_history = {}
        self.title = ""
        self.stream_start = ""
        self.is_live = False

        self.blacklist_file = "blacklists/{}_blacklist.txt".format(self.channel)
        with open(self.blacklist_file, "a+") as fin:
            self.blacklist = [x.strip() for x in fin.readlines()]

        self.commands = {}
        self.setup_commands(config)
        self.social = {}
        self.setup_social(config)
        self.toobou = {}
        self.setup_toobou(config)

    def setup_social(self, config):
        self.social = {}
        self.social = {
            "active": config["settings"]["social_active"],
            "last_send": time.time(),
            "message_interval": config["settings"]["social_messages"] or 30,
            "time_interval": config["settings"]["social_time"] or 10,
            "output": config["settings"]["social_output"]
        }

    def setup_toobou(self, config):
        self.toobou = {}
        self.toobou = {
            "active": config["settings"]["toobou_active"],
            "trigger": config["settings"]["toobou_trigger"],
            "last": 0,
            "limit": config["settings"]["toobou_limit"] or 30,
            "output": config["settings"]["toobou_output"]
        }

    def setup_commands(self, config):
        # Wipe the dict clean first so that it may be called at anytime for a clean commands build
        self.commands = {}
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

    def update_config(self, new_config):
        self.config = new_config
        self.setup_commands(new_config)
        self.setup_social(new_config)
        self.setup_toobou(new_config)

    def process_message(self, c_msg):
        self.action_functions[c_msg["action"]](c_msg)

    def privmsg(self, c_msg):
        pass

    def notice(self, c_msg):
        pass

    def hosttarget(self, c_msg):
        pass

    def clearchat(self, c_msg):
        pass

    def userstate(self, c_msg):
        self.is_mod = bool(int(c_msg["tags"]["mod"]))

    def globaluserstate(self, c_msg):
        pass

    def roomstate(self, c_msg):
        pass

    def join(self, c_msg):
        pass

    def part(self, c_msg):
        pass

    def mode(self, c_msg):
        pass

    def reconnect(self, c_msg):
        pass
