#! /usr/bin/env python2.7

import ast
import datetime
import imp
import logging
import os
import sys
import time

import pytz

from   modules.module_errors import DeactivatedBotException
from   modules.apis import kraken
from   modules.apis import newbs
from   modules.apis import osu
from   modules.apis import splits_io
from   modules.apis import sr_com
from   modules.apis import srl
from   modules.apis import youtube
from   modules.commands import help as help_command

command_functions = {}

def init_commands():
    cmd_filenames = []
    cmd_folder = os.path.join(os.path.dirname(__file__), "commands")

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
            command_functions[cmd_name] = module
        except Exception, e:
            print "Error importing {0}.".format(imp_name)
            print e

init_commands()

class SaltyBot(object):

    elevated_user = ["staff", "admin", "global_mod", "mod"]

    def __init__(self, config):
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
            "ROOMSTATE"       : self.roomstate,
            "CAP"             : self.cap,
            "USERNOTICE"      : self.usernotice
        }
        self.super_users = ast.literal_eval(os.environ["salty_super_users"])
        self.super_users = [x.strip() for x in self.super_users]

        self.config = config

        self.twitch_api = kraken.Kraken(headers={"User-Agent" : "SaltyBot"})
        self.osu_api = osu.OsuAPI()
        self.newbs_api = newbs.NewbsAPI(cookies={"session" : config["session"]})
        self.srl_api = srl.SRLAPI()
        self.sr_com_api = sr_com.SRcomAPI()
        self.splits_io_api = splits_io.SplitsIOAPI()
        self.youtube_api = youtube.YoutubeAPI()

        self.is_mod = False
        self.messages_received = 0

        self.user_id = config["id"]
        self.session_id = config["session"]

        if self.config["bot_oauth"]:
            self.bot_nick = config["bot_nick"]
            self.bot_oauth = config["bot_oauth"]
        else:
            self.bot_nick = os.environ["default_bot_nick"]
            self.bot_oauth = os.environ["default_bot_oauth"]
        self.channel = config["twitch_name"]

        if config["speedruncom_nick"]:
            self.speedruncom_nick = config["speedruncom_nick"].lower()
        else:
            self.speedruncom_nick = self.channel

        self.game = ""
        self.game_history = {}
        self.title = ""
        self.stream_start = ""
        self.is_live = False

        self.highlights = []

        self.blacklist_file = "blacklists/{}_blacklist.txt".format(self.channel)
        with open(self.blacklist_file, "a+") as fin:
            self.blacklist = [x.strip() for x in fin.readlines()]

        self.votes = {}

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
            "last_message": 0,
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
            "custom": True,
            "last": 0,
            "limit": 300,
            "mod_req": False,
            "output": "Powered by SaltyBot, for a full list of command check out the github repo http://bombch.us/z3x or to get it in your channel go here http://bombch.us/z3y"
        }
        self.commands["!help"] = {
            "custom": False,
            "last": 0,
            "limit": 2,
            "mod_req": False,
            "function": help_command.call,
            "help_text": help_command.HELP_TEXT
        }
        for i in config["commands"]:
            if i["on"]:
                curr_com = "!{}".format(i["name"])
                self.commands[curr_com] = {
                    "custom": False,
                    "last": 0,
                    "limit": i["limit"] or 30,
                    "mod_req": bool(i["admin"]),
                    "function": command_functions[curr_com].call,
                    "help_text": command_functions[curr_com].HELP_TEXT
                }
        for i in config["custom_commands"]:
            command = "!{0}".format(i["trigger"])
            if self.commands.get(command, None):
                continue
            if i["on"]:
                self.commands[command] = {
                    "custom": True,
                    "last": 0,
                    "limit": i["limit"] or 30,
                    "mod_req": bool(i["admin"]),
                    "output": i["output"],
                    "help_text": [command, i["help_text"]]
                }

        self.votes = {}
        if config["settings"]["voting_active"]:
            self.commands["!createvote"] = {
                "custom": False,
                "last": 0,
                "limit": 0,
                "mod_req": True,
                "function": command_functions["!createvote"].call,
                "help_text": command_functions["!createvote"].HELP_TEXT
            }
            self.commands["!vote"] = {
                "custom": False,
                "last": 0,
                "limit": 0,
                "mod_req": False,
                "function": command_functions["!vote"].call,
                "help_text": command_functions["!vote"].HELP_TEXT
            }
            self.commands["!checkvote"] = {
                "custom": False,
                "last": 0,
                "limit": 15,
                "mod_req": False,
                "function": command_functions["!checkvote"].call,
                "help_text": command_functions["!checkvote"].HELP_TEXT
            }
            self.commands["!endvote"] = {
                "custom": False,
                "last": 0,
                "limit": 0,
                "mod_req": True,
                "function": command_functions["!endvote"].call,
                "help_text": command_functions["!endvote"].HELP_TEXT
            }

    def update_config(self, new_config):
        if self.config["settings"]["active"] and not new_config["settings"]["active"]:
            raise DeactivatedBotException

        self.session_id = new_config["session"]
        self.newbs_api.cookies["session"] = new_config["session"]
        self.config = new_config
        self.setup_commands(new_config)
        self.setup_social(new_config)
        self.setup_toobou(new_config)

    def update_twitch_info(self, new_info):
        if new_info["game"] and self.game != new_info["game"]:
            if self.game:
                self.game_history[self.game]["end"] = datetime.datetime.now(pytz.utc)
            self.game_history[new_info["game"]] = {}
            self.game_history[new_info["game"]]["start"] = datetime.datetime.now(pytz.utc)
        elif not new_info["game"]:
            self.game_history = {}
        self.game = new_info["game"]

        if new_info["title"]:
            self.title = new_info["title"]

        self.stream_start = new_info["stream_start"]
        self.is_live = new_info["is_live"]


    def check_permissions(self, c_msg):
        try:
            command = c_msg["message"].split(" ", 1)[0]
        except IndexError:
            return False
        if not self.commands.get(command, None):
            return False

        if c_msg["sender"] in self.super_users:
            return True

        if self.commands[command]["mod_req"]:
            if not c_msg["tags"]["mod"] and not c_msg["sender"] == self.channel:
                return False

        if (time.time() - self.commands[command]["last"]) < self.commands[command]["limit"]:
            return False

        return True


    def process_message(self, c_msg):
        return self.action_functions[c_msg["action"]](c_msg)

    def privmsg(self, c_msg):
        self.messages_received += 1
        msg_split = c_msg["message"].split(" ")
        command = msg_split[0]

        if command not in command_functions.keys() and command not in self.commands.keys():
            return False
        try:
            if not self.check_permissions(c_msg):
                return False
            if self.commands[command]["custom"]:
                success, response = True, self.commands[command]["output"]
            else:
                success, response = self.commands[command]["function"](self, c_msg)
        except Exception, e:
            logging.error("{0} triggered an error.".format(command))
            logging.exception(e)
            return

        if success:
            self.commands[command]["last"] = time.time()
        return response

    def notice(self, c_msg):
        pass

    def hosttarget(self, c_msg):
        pass

    def clearchat(self, c_msg):
        pass

    def userstate(self, c_msg):
        self.is_mod = (
            self.channel == self.bot_nick or
            bool(int(c_msg["tags"]["mod"])) or
            bool(c_msg["tags"]["user-type"])
        )

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

    def cap(self, c_msg):
        pass

    def usernotice(self, c_msg):
        pass
