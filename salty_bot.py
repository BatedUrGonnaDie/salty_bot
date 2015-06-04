#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-

import datetime
import json
import logging
import Queue as Q
import random
import re
import socket
import sys
import threading
import time
import traceback

import isodate
import pytz
import requests

import modules.irc as irc
import salty_listener as SaltyListener

debuging = True
development = False

RESTART = "<restart>"
CHECK = "<check threads>"
UPDATE = "<update>"

TYPE = 0
DATA = 1

interface = Q.Queue()

#Set up all the global variables
with open('general_config.json', 'r') as data_file:
    general_config = json.load(data_file, encoding='utf-8')

lol_api_key = general_config['general_info']['lol_api_key']
youtube_api_key = general_config['general_info']['youtube_api_key']
osu_api_key = general_config['general_info']['osu']['osu_api_key']
osu_irc_nick = general_config['general_info']['osu']['osu_irc_nick']
osu_irc_pass = general_config['general_info']['osu']['osu_irc_pass']
db_url = general_config['general_info']['db_url']
default_nick = general_config['general_info']['default_nick']
default_oauth = general_config['general_info']['default_oauth']

if development:
    web_listen_ip = "localhost"
else:
    web_listen_ip = general_config['general_info']["web_listen_ip"]

web_listen_port = general_config['general_info']["web_listen_port"]
web_secret = general_config["general_info"]["web_secret"]
#super users are used for bot breaking commands and beta commands
SUPER_USER = general_config['general_info']['super_users']


logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG, format="[%(levelname)s %(asctime)s] %(message)s", datefmt="%m-%d %H:%M:%S")
logging.getLogger("requests").setLevel(logging.WARNING)

class SaltyBot(object):

    message_limit = 100
    elevated_user = ["staff", "admin", "global_mod", "mod"]

    def __init__(self, config_data, debug = False, irc_obj = None):
        if config_data["bot_oauth"] == None:
            config_data["bot_nick"] = default_nick
            config_data["bot_oauth"] = default_oauth

        self.twitch_nick = config_data["bot_nick"]
        self.twitch_oauth = config_data["bot_oauth"]
        if not self.twitch_oauth.startswith("oauth:"):
            self.twitch_oauth = "oauth:" + self.twitch_oauth

        self.__DB = debug
        self.running = True
        self.messages_received = 0
        self.rate_limit = 0
        self.session = config_data["session"]
        self.user_id = config_data["id"]
        self.config_data = config_data
        if not irc_obj:
            self.irc = irc.IRC("irc.twitch.tv", 443, self.twitch_nick, self.twitch_oauth)
        else:
            self.irc = irc_obj

        self.channel = config_data["twitch_name"]
        if config_data["speedruncom_nick"]:
            self.speedruncom_nick = config_data["speedruncom_nick"].lower()
        else:
            self.speedruncom_nick = self.channel
        self.game = ''
        self.title = ''
        self.time_start = ''
        self.stream_online = False
        self.commands = []
        self.admin_commands = []
        self.custom_commands = []
        self.blacklist = []
        self.votes = {}
        self.to_highlight = []
        self.review = {"quote": [], "pun": []}
        self.last_text = {"quote": "", "pun": ""}
        self.t_trig = None
        with open('blacklists/{}_blacklist.txt'.format(self.channel), 'a+') as data_file:
            blacklist = data_file.readlines()
        for i in blacklist:
            self.blacklist.append(i.split('\n')[0])
        self.command_times = {}
        self.custom_command_times = {}

    def start(self):
        self.thread = threading.Thread(target=self.twitch_run)
        self.thread.setDaemon(True)
        self.thread.start()

        return self.thread

    def twitch_info(self, game, title, live, online_status):
        #Game and title need to be a string to work
        self.game = game.lower()
        self.game_normal = game
        self.title = title.lower()
        self.time_start = live
        self.stream_online = online_status

    def twitch_connect(self):
        #Connect to Twitch IRC
        if not self.irc.connected:
            if self.__DB:
                print "Joining {} as {}.\n".format(self.channel,self.twitch_nick)
            try:
                #If it fails to conenct try again in 60 seconds
                self.irc.create()
                self.irc.connect()
                self.irc.recv(4096)
            except Exception:
                print '{} failed to connect.'.format(self.channel)
                traceback.print_exc(limit=2)
                time.sleep(60)
                self.twitch_connect()

            self.irc.capability("twitch.tv/tags twitch.tv/commands")
            self.irc.recv(1024)
            self.irc.join(self.channel)
        else:
            if self.__DB:
                print "{} already connected.\n".format(self.channel)

    def twitch_commands(self):
        #Set up all the limits, if its admin, if its on, quote and pun stuff, and anything else that needs setting up for a command
        self.command_times["!bot_info"] = {"last": 0, "limit": 300}
        self.commands.append("!bot_info")

        for i in self.config_data["commands"]:
            if i["on"]:
                curr_com = "!" + i["name"]
                if i["admin"]:
                    self.admin_commands.append(curr_com)
                else:
                    self.commands.append(curr_com)
                self.command_times[curr_com] = {"last": 0, "limit": i["limit"] or 30}

        if self.config_data["social_active"]:
            self.command_times["social"] = {"time_last": int(time.time()),
                                            "messages": self.config_data["social_messages"] or 0,
                                            "messages_last": self.messages_received,
                                            "time": self.config_data["social_time"] or 0}
            self.social_text = self.config_data["social_output"]

        if self.config_data["toobou_active"]:
            self.t_trig = self.config_data["toobou_trigger"]
            self.command_times["toobou"] = {"trigger": self.t_trig,
                                            "last": 0,
                                            "limit": self.config_data["toobou_limit"] or 1}

        for i in self.config_data["custom_commands"]:
            if i["on"]:
                self.custom_commands.append("!{}".format(i["trigger"]))
                self.custom_command_times["!{}".format(i["trigger"])] = {"last": 0,
                                                                        "limit": i["limit"] or 30,
                                                                        "output": i["output"],
                                                                        "admin": i["admin"]}

    def live_commands(self):
        # Remove any commands that would not currently work when !commands is used
        # Type cast to not mess with the original lists
        active_commands = list(self.commands) + list(self.custom_commands)
        admin_commands_tmp = list(self.admin_commands)

        if not self.time_start:
            try:
                active_commands.remove('!uptime')
            except Exception:
                pass

        if self.config_data["voting_active"] and self.votes:
            active_commands.append("!checkvotes")
        else:
            try:
                active_commands.remove("!vote")
            except Exception:
                pass

        if self.config_data["voting_active"]:
            if self.config_data["voting_mods"]:
                admin_commands_tmp.append("!createvote")
                admin_commands_tmp.append("!endvote")

        if self.game == '':
            try:
                active_commands.remove('!leaderboard')
            except Exception:
                pass

        if self.game != 'osu!':
            try:
                active_commands.remove('!rank')
            except Exception:
                pass
            try:
                active_commands.remove('!song')
            except Exception:
                pass

        if self.game != 'league of legends':
            try:
                active_commands.remove('!runes')
            except Exception:
                pass
            try:
                active_commands.remove('!masteries')
            except Exception:
                pass

        if 'race' not in self.title and 'racing' not in self.title:
            try:
                active_commands.remove('!race')
            except Exception:
                pass

        command_string = ', '.join(sorted(active_commands))
        if self.admin_commands:
            command_string += " | Mod Only Commands: " + ", ".join(sorted(admin_commands_tmp))
        if command_string == '!bot_info, !commands':
            self.twitch_send_message('There are no current active commands.', '!commands')
        else:
            self.twitch_send_message(command_string, '!commands')

    def clear_limiter(self):
        self.rate_limit = 0

    def twitch_send_message(self, response, command = None):
        #Sending any message to chat goes through this function
        try:
            response = response.encode('utf-8')
        except Exception:
            pass
        if response.startswith('/me') or response.startswith('.me'):
            #Grant exception for /me because it can't do any harm
            pass
        elif response.startswith('.') or response.startswith('/'):
            #Prevent people from issuing server commands since bot is usually mod (aka /ban)
            response = "Please stop trying to abuse me BibleThump (messages cannot start with '/' or '.')"
            command = ''

        if self.rate_limit < self.message_limit:
            self.irc.privmsg(self.channel, response)
            self.rate_limit += 1
        else:
            print "{} has exceeded the IRC rate limit".format(self.channel)
            return

        if self.__DB == True:
            try:
                db_message = '#' + self.channel + ' ' + self.twitch_nick + ": " + response.decode('utf-8')
                db_message = db_message.encode('utf-8')
                print datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ') + db_message
            except Exception:
                print("Message contained unicode, could not display in terminal\n\n")

        if command:
            #Update when the command was last used for rate limiting
            self.command_times[command]['last'] = int(time.time())

    def command_check(self, c_msg, command):
        #Finds if the user can use said command, and then if the command is off cooldown
        #Will only return True if it's off cooldown and the user has the priviledges for the command
        if command in self.commands or command in self.admin_commands:
            if c_msg["sender"] == self.channel or c_msg["sender"] in SUPER_USER:
                return True
            if command in self.admin_commands:
                if c_msg["tags"]["user_type"] in self.elevated_user:
                    return True
            else:
                if self.time_check(command):
                    return True
        return False

    def time_check(self, command):
        #Return the current time minus the time the command was last used (used to make sure its off cooldown)
        return int(time.time()) - self.command_times[command]['last'] >= self.command_times[command]['limit']

    def api_caller(self, url, headers = None):
        #Call JSON api's for other functions
        if self.__DB: print url

        try:
            data = requests.get(url, headers = headers)
            if data.status_code == 200:
                data_decode = data.json()
                return data_decode
            else:
                print data
                return False
        except Exception:
            traceback.print_exc(limit=2)
            return False

    def osu_api_user(self):
        #Perform a simple check of basic user stats on osu
        osu_nick = self.config_data["osu_nick"]
        url = 'https://osu.ppy.sh/api/get_user?k={}&u={}'.format(osu_api_key, osu_nick)
        data_decode = self.api_caller(url)
        if data_decode == False:
            return
        data_decode = data_decode[0]
        username = data_decode['username']
        level = data_decode['level']
        level = round(float(level))
        level = int(level)
        accuracy = data_decode['accuracy']
        accuracy = round(float(accuracy), 2)
        pp_rank = data_decode['pp_rank']

        response = '{} is level {} with {}% accuracy and ranked {}.'.format(username, level, accuracy, pp_rank)
        self.twitch_send_message(response)

    def osu_song_display(self):
        url = 'https://leagueofnewbs.com/api/users/{}/songs'.format(self.channel)
        data_decode = self.api_caller(url)
        if data_decode:
            print data_decode

    def osu_link(self, c_msg):
        #Sends beatmaps linked in chat to you on osu, and then displays the map title and author in chat
        osu_nick = self.config_data["osu_nick"]

        if c_msg["message"].find('osu.ppy.sh/s/') != -1:
            osu_number = 's=' + c_msg["message"].split('osu.ppy.sh/s/')[-1].split(' ')[0]
        elif c_msg["message"].find('osu.ppy.sh/b/') != -1:
            osu_number = 'b=' + c_msg["message"].split('osu.ppy.sh/b/')[-1].split(' ')[0]

        osu_send_message(osu_irc_pass, osu_nick, c_msg["message"], c_msg["sender"])

        url = 'https://osu.ppy.sh/api/get_beatmaps?k={}&{}'.format(osu_api_key, osu_number)
        data_decode = self.api_caller(url)
        if data_decode == False:
            self.twitch_send_message("There was a problem retrieving the map info from the Osu! API")
            return
        data_decode = data_decode[0]

        response = '{} - {}, mapped by {}'.format(data_decode['artist'], data_decode['title'], data_decode['creator'])
        self.twitch_send_message(response)

    def format_sr_time(self, f_time):
        m, s = divmod(float(f_time), 60)
        h, m = divmod(int(m), 60)
        s = round(s, 2)
        if s < 10:
            s = '0' + str(s)
        if m < 10:
            m = '0' + str(m)
        time = '{}:{}:{}'.format(int(h), m, s)
        if time.endswith(".0"):
            time = time[:-2]
        if time.startswith("0:"):
            time = time[2:]
        if time.startswith("0"):
            time = time[1:]
        if self.__DB:
            print time
        return time

    def get_number_suffix(self, number):
        return 'th' if 11 <= number <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')

    def find_active_cat(self, sr_game, game_records):
        # Returns True or False depending on if success or failure, and a string
        # String will be the error message to send to chat if failure or the actice cat if success
        categories_in_title = []
        category_position = {}
        if sr_game.lower() == self.game.lower():
            sr_game_cats = game_records[sr_game].keys()
            for i in sr_game_cats:
                if i.lower() in self.title:
                    categories_in_title.append(i)
            categories_in_title = list(set(categories_in_title))
        else:
            response = "It appears the game is not on speedrun.com BibleThump"
            return False, response

        if len(categories_in_title) == 0:
            response = "I'm sorry, but I could not find a category in the title that exists on speedrun.com"
            return False, response
        elif len(categories_in_title) > 1:
            categories_in_title = list(set(categories_in_title))

        if len(categories_in_title) > 1:
            for j in categories_in_title:
                category_position[j] = self.title.find(j.lower())
            min_value = min(category_position.itervalues())
            min_keys = [k for k in category_position if category_position[k] == min_value]
            active_cat = sorted(min_keys, key = len)[-1]
        else:
            active_cat = categories_in_title[0]

        return True, active_cat

    def pb_retrieve(self, c_msg):
        msg_split = c_msg["message"].split(' ', 3)
        infer_category = False

        if msg_split[0] != "pb":
            return

        try:
            url = "http://www.speedrun.com/api_records.php?user={}".format(msg_split[1])
            user_name = msg_split[1]
            try:
                url += "&game=" + msg_split[2]
                try:
                    msg_split[3]
                except IndexError:
                    if self.title != '':
                        infer_category = True
                    else:
                        self.twitch_send_message("Please specify a category to look up.")
                        return
            except IndexError:
                if self.game != '':
                    url += "&game=" + self.game
                else:
                    self.twitch_send_message("Please specify a game shortcode to look up on speedrun.com")
                    return
        except IndexError:
            if self.game != '' and self.title != '':
                url = "http://speedrun.com/api_records.php?user={}&game={}".format(self.speedruncom_nick, self.game)
                user_name = self.speedruncom_nick
                infer_category = True
            else:
                response = "Please either provide a player, game, and category or wait for the streamer to go live."
                self.twitch_send_message(response, "!pb")
                return

        game_data = self.api_caller(url)
        if game_data == False:
            self.twitch_send_message("There was an error fetching info from speedrun.com", "!pb")
            return

        try:
            sr_game = dict(game_data).keys()[0]
        except TypeError:
            self.twitch_send_message("This game does not seem to exist on speedrun.com", "!pb")
            return

        if infer_category:
            success, response_string = self.find_active_cat(sr_game, game_data)
            if success == False:
                self.twitch_send_message(response_string, "!pb")
                return
            else:
                active_cat = response_string
        else:
            game_cats = game_data[sr_game].keys()
            for i in game_cats:
                if msg_split[3].lower() == i.lower():
                    active_cat = i
                    break
            try:
                active_cat
            except NameError:
                self.twitch_send_message("Please specify a category that is available on speedrun.com", "!pb")
                return

        cat_record = game_data[sr_game][active_cat]
        pb_time = self.format_sr_time(cat_record["time"])
        place = str(cat_record["place"]) + self.get_number_suffix(int(cat_record["place"]))
        msg = "{}'s pb for {} {} is {}.  They are ranked {} on speedrun.com".format(user_name.capitalize(), sr_game, active_cat, pb_time, place)
        self.twitch_send_message(msg, "!pb")

    def wr_retrieve(self, c_msg):
        #Find the categories that are on file in the title, and then if more than one exist pick the one located earliest in the title
        msg_split = c_msg["message"].split(' ', 2)

        if msg_split[0] != "wr":
            return

        try:
            url = "http://www.speedrun.com/api_records.php?game=" + msg_split[1]
            try:
                msg_split[2]
            except IndexError:
                self.twitch_send_message("Please provide a category to search for.")
                return
        except IndexError:
            if self.game != '':
                url = "http://www.speedrun.com/api_records.php?game=" + self.game
            else:
                self.twitch_send_message("Please either provide a game and category or wait for the streamer to go live.")
                return

        game_records = self.api_caller(url)
        if game_records == False:
            self.twitch_send_message("There was an error fetching info from speedrun.com", '!wr')
            return
        try:
            sr_game = dict(game_records).keys()[0]
        except TypeError:
            self.twitch_send_message("This game does not seem to exist on speedrun.com", '!wr')
            return

        if len(msg_split) == 1:
            success, response_string = self.find_active_cat(sr_game, game_records)
            if success == False:
                self.twitch_send_message(response_string, "!wr")
                return
            else:
                active_cat = response_string

        elif len(msg_split) == 3:
            game_cats = game_records[sr_game].keys()
            for i in game_cats:
                if msg_split[2].lower() == i.lower():
                    active_cat = i
                    break
            try:
                active_cat
            except NameError:
                self.twitch_send_message("Please specify a category that is available on speedrun.com", '!wr')
                return

        cat_record = game_records[sr_game][active_cat]
        try:
            wr_time = self.format_sr_time(cat_record['time'])
        except TypeError:
            wr_time = ""
        try:
            wr_ingame = self.format_sr_time(cat_record["timeigt"])
            if wr_time:
                wr_time = "{0} real time and {1} ingame time ".format(wr_time, wr_ingame)
            else:
                wr_time = wr_ingame
        except KeyError:
            wr_ingame = ""
        msg = "The current world record for {0} {1} is {2} by {3}.".format(sr_game, active_cat, wr_time, cat_record['player'])
        if cat_record['video']:
            msg += "  Video: {0}".format(cat_record['video'])
        if cat_record["splitsio"]:
            msg += " Splits: {0}".format(cat_record["splitsio"])
        self.twitch_send_message(msg, '!wr')

    def leaderboard_retrieve(self):
        #Retrieve leaderboard for game as set on Twitch
        game_no_spec = re.sub(' ', '_', self.game_normal)
        game_no_spec = re.sub("[:]", '', game_no_spec)
        url = 'http://speedrun.com/' + game_no_spec
        self.twitch_send_message(url, '!leaderboard')

    def splits_check(self, c_msg):
        # Get pbs from splits.io, find the correct category
        msg_split = c_msg["message"].split(' ', 3)

        if msg_split[0] != "splits":
            return

        game_type = "name"
        infer_category = False
        try:
            url = "https://splits.io/api/v3/users/{}/pbs".format(msg_split[1])
            user_name = msg_split[1]
            try:
                input_game = msg_split[2]
                game_type = "shortname"
                try:
                    category = msg_split[3]
                except IndexError:
                    if self.title != "":
                        infer_category = True
                    else:
                        self.twitch_send_message("Please wait for the streamer to go live or specify a category.")
                        return
            except IndexError:
                if self.game != "" and self.title != "":
                    input_game = self.game
                    infer_category = True
                else:
                    self.twitch_send_message("Please wait for the streamer to go live or specify a game and category.")
                    return
        except IndexError:
            if self.game != "" and self.title != "":
                url = "https://splits.io/api/v3/users/{}/pbs".format(self.channel)
                user_name = self.channel
                input_game = self.game
                infer_category = True
            else:
                self.twitch_send_message("Please wait for the streamer to go live or specify a user, game, and category.")
                return

        splits_response = self.api_caller(url)
        if splits_response == False:
            self.twitch_send_message("Failed to retrieve data from splits.io, please try again.")
            return

        if infer_category:
            games_with_category = []
        for i in splits_response["pbs"]:
            try:
                if i["game"][game_type].lower() == input_game:
                    output_game = i["game"]["name"]
                    if infer_category:
                        if i["category"]["name"].lower() in self.title:
                            games_with_category.append(i["category"]["name"])
                    else:
                        if category == i["category"]["name"].lower():
                            pb_splits = i
                            active_cat = i["category"]["name"]
                            break
            except AttributeError:
                continue

        if infer_category:
            while True:
                games_with_category = list(set(games_with_category))
                if len(games_with_category) == 0:
                    self.twitch_send_message("I could not find splits based on any categories in the title.", "!splits")
                    return
                elif len(games_with_category) == 1:
                    active_cat = games_with_category[0]
                    for i in splits_response["pbs"]:
                        try:
                            if input_game == i["game"][game_type].lower():
                                if active_cat == i["category"]["name"]:
                                    pb_splits = i
                        except AttributeError:
                            continue
                    break
                else:
                    category_position = {}
                    for j in games_with_category:
                        category_position[j["category"]["name"]] = self.title.find(j["category"]["name"].lower())
                    min_value = min(category_position.itervalues())
                    min_keys = [k for k in category_position if category_position[k] == min_value]
                    active_cat = sorted(min_keys, key = len)[-1]
                    for i in splits_response["pbs"]:
                        if active_cat == i["category"]["name"]:
                            pb_splits = i
                    break

        try:
            pb_splits
        except NameError:
            if infer_category:
                self.twitch_send_message("I could not find splits based on any categories in the title.", "!splits")
                return
            else:
                self.twitch_send_message("I could not find splits based on the category provided.", "!splits")
                return

        time = self.format_sr_time(pb_splits['time'])
        link_to_splits = 'https://splits.io{}'.format(pb_splits['path'])
        response = "{}'s best splits for {} {} is {} {}".format(user_name.capitalize(), output_game, active_cat, time, link_to_splits)
        self.twitch_send_message(response, '!splits')

    def add_text(self, c_msg, text_type):
        #Add a pun or quote to the review file
        text = c_msg["message"][(len(text_type) + 4):]
        text = text.strip()

        if text == 'add{}'.format(text_type) or text == 'add{} '.format(text_type):
            self.twitch_send_message('Please input a {}.'.format(text_type))
        else:
            url = "https://leagueofnewbs.com/api/users/{}/{}s".format(self.channel, text_type)
            data = {"reviewed": 1 if c_msg["sender"] == self.channel else 0,
                    "text": text,
                    "user_id": self.channel}
            cookies = {"session": self.session}

            success = requests.post(url, data=data, cookies=cookies)
            try:
                success.raise_for_status()
                reviewed = "to the database" if c_msg["sender"] == self.channel else "for review"
                response = "Your {} has been added {}.".format(text_type, reviewed)
            except Exception:
                traceback.print_exc(limit=2)
                response = "I had problems adding this to the database."
            self.twitch_send_message(response, "!add" + text_type)

    def text_retrieve(self, text_type):
        #Pull a random pun/quote from the database
        #Will not pull the same one twice in a row
        text_type_plural = text_type + 's'
        url = "https://leagueofnewbs.com/api/users/{}/{}?limit=2".format(self.channel, text_type_plural)
        text_lines = self.api_caller(url)
        if text_lines:
            try:
                if text_lines[text_type_plural][0]["text"] != self.last_text[text_type]:
                    response = text_lines[text_type_plural][0]["text"]
                else:
                    try:
                        response = text_lines[text_type_plural][1]["text"]
                    except IndexError:
                        response = text_lines[text_type_plural][0]["text"]
            except IndexError:
                response = "Please insert {} into the database before using this command.".format(text_type_plural)
        else:
            response = "There was a problem retrieving {}.".format(text_type_plural)

        self.twitch_send_message(response, '!' + text_type)
        self.last_text[text_type] = response

    def srl_race_retrieve(self):
        #Goes through all races, finds the race the user is in, gathers all other users in the race, prints the game, the
        #category people are racing, the time racebot has, and either a multitwitch link or a SRL race room link
        srl_nick = self.config_data["srl_nick"].lower()
        url = 'http://api.speedrunslive.com/races'
        data_decode = self.api_caller(url)
        if data_decode == False:
            return
        data_races = data_decode['races']
        srl_race_entrants = []
        for i in data_races:
            if srl_nick in [x.lower() for x in i["entrants"]]:
                race_channel = i
                for values in race_channel['entrants'].values():
                    if values['statetext'] == 'Ready' or values['statetext'] == 'Entered':
                        if values['twitch'] != '':
                            srl_race_entrants.append(values['twitch'].lower())
                user_place = race_channel['entrants'][srl_nick]['place']
                user_time = race_channel['entrants'][srl_nick]['time']
                srl_race_game = race_channel['game']['name']
                srl_race_category = race_channel['goal']
                srl_race_status = race_channel['statetext']
                srl_race_time = race_channel['time']
                srl_race_link = 'http://www.speedrunslive.com/race/?id={}'.format(race_channel['id'])
                srl_live_entrants = []
                live_decoded = self.api_caller('https://api.twitch.tv/kraken/streams?channel=' + ','.join(srl_race_entrants))
                for j in live_decoded['streams']:
                    srl_live_entrants.append(j['channel']['name'])
                response = 'Game: {}, Category: {}, Status: {}'.format(srl_race_game, srl_race_category, srl_race_status)
                if srl_race_time > 0:
                    if user_time > 0:
                        time_formatted = self.format_sr_time(user_time)
                        position_suffix = str(self.get_number_suffix(user_place))
                        response += ', Finished {}{} with a time of {}'.format(user_place, position_suffix, time_formatted)
                    else:
                        real_time = (int(time.time()) - srl_race_time)
                        time_formatted = self.format_sr_time(real_time)
                        response += ', RaceBot Time: {}'.format(time_formatted)
                live_length = len(srl_live_entrants)
                if srl_race_status == 'Complete':
                    response += '.  {}'.format(srl_race_link)
                elif live_length <= 6 and live_length > 1:
                    multitwitch_link = "http://kadgar.net/live/" + '/'.join(srl_live_entrants)
                    response += '.  {}'.format(multitwitch_link)
                else:
                    response += '.  {}'.format(srl_race_link)
                self.twitch_send_message(response, '!race')
                return

    def youtube_video_check(self, c_msg):
        #Links the title and uploader of the youtube video in chat
        video_ids = re.findall("(?:youtube(?:-nocookie)?\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})", c_msg["message"])
        if not video_ids:
            return
        else:
            seen_ids = set()
            seen_add = seen_ids.add
            video_ids = [x for x in video_ids if not (x in seen_ids or seen_add(x))]

        final_list = []
        for i in video_ids:
            url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id={}&key={}'.format(i, youtube_api_key)
            data_decode = self.api_caller(url)

            if data_decode == False:
                return

            if len(data_decode['items']) != 0:
                data_items = data_decode['items']
                video_title = data_items[0]['snippet']['title'].encode("utf-8")
                uploader = data_items[0]['snippet']['channelTitle'].encode("utf-8")
                view_count = data_items[0]['statistics']['viewCount']
                duration = isodate.parse_duration(data_items[0]["contentDetails"]["duration"])
                duration_string = self.format_sr_time(duration.seconds)
                final_list.append("[{}] {} uploaded by {}. Views: {}".format(duration_string, video_title, uploader, view_count))
            else:
                continue

        self.twitch_send_message(" | ".join(final_list))
        return

    def create_vote(self, c_msg):
        #Used to create polls in chat
        #Creating polls requires a pretty specific syntax, but makes it easy to have different types
        if self.votes:
            self.twitch_send_message('There is already an open poll, please close it first.')
            return

        poll_type = c_msg["message"].split(' ')[1]

        try:
            poll = re.findall('"(.+)"', c_msg["message"])[0]
        except Exception:
            self.twitch_send_message('Please give the poll a name.')
            return

        self.votes = {  'name' : poll,
                        'type' : poll_type,
                        'options' : {},
                        'voters' : {}}

        if poll_type == 'strict':
            options = re.findall('\((.+?)\)', c_msg["message"])

            if not options:
                self.twitch_send_message('You did not supply any options, poll will be closed.')
                self.votes.clear()
                return

            for i in options:
                vote_option = i.lower()
                self.votes['options'][vote_option] = 0
            response = 'You may now vote for this poll using only the supplied options.'

        elif poll_type == 'loose':
            response = 'You may now vote for this poll with whatever choice you like.'

        else:
            response = "Please specify a poll type."
            self.votes.clear()

        self.twitch_send_message(response)

    def end_vote(self):
        #Ending a current poll will display the winning vote of the poll and close it
        if self.votes:
            try:
                winning_amount = max(self.votes['options'].values())
                winning_keys = [key for key, value in self.votes["options"] if value == winning_amount]
                if len(winning_keys) == 0:
                    response = ""
                elif len(winning_keys) == 1:
                    response = response = "{} has won with {} votes.".format(winning_keys[0], winning_amount)
                else:
                    combined_keys = ", ".join(winning_keys)
                    "{} have all tied with {} votes!".format(combined_keys, winning_amount)
            finally:
                self.votes.clear()

            if response:
                self.twitch_send_message(response)

    def vote(self, c_msg):
        #Allows viewers to vote in a poll created by mods/broadcaster
        try:
            sender_bet = c_msg["message"].split('vote ')[-1]
            sender_bet = sender_bet.lower()
        except Exception:
            return
        if not self.votes:
            return

        if self.votes['type'] == 'strict':
            if sender_bet not in self.votes['options']:
                self.twitch_send_message('You must vote for one of the options specified: ' + ', '.join(self.votes['options'].keys()), '!vote')
                return

        if c_msg["sender"] in self.votes['voters']:
            if sender_bet == self.votes['voters'][c_msg["sender"]]:
                response = 'You have already voted for that {}.'.format(c_msg["sender"])
            else:
                previous = self.votes['voters'][c_msg["sender"]]
                self.votes['options'][previous] -= 1

                if self.votes['options'][previous] == 0 and self.votes['type'] == 'loose':
                    del self.votes['options'][previous]

                try:
                    self.votes['options'][sender_bet] += 1
                except KeyError:
                    self.votes['options'][sender_bet] = 1

                self.votes['voters'][c_msg["sender"]] = sender_bet
                response = '{} has changed their vote to {}'.format(c_msg["sender"], sender_bet)
        else:
            try:
                self.votes['options'][sender_bet] += 1
            except KeyError:
                self.votes['options'][sender_bet] = 1

            self.votes['voters'][c_msg["sender"]] = sender_bet
            response = '{} now has {} votes for it.'.format(sender_bet, str(self.votes['options'][sender_bet]))

        self.twitch_send_message(response, '!vote')

    def check_votes(self):
        #Allows you to see what is currently winning in the current poll w/o closing it
        if not self.votes:
            return

        response = 'Current poll: "{}".  '.format(self.votes["name"])
        if not self.votes['options']:
            response += "No one has bet yet.  "
        else:
            for k, v in self.votes["options"].items():
                response += "{}: {}; ".format(k, v)

        self.twitch_send_message(response[:-2], '!vote')

    def text_review(self, c_msg, last_r = 'none'):
        #Review puns/quotes through chat (spammy as shit)
        try:
            text_type = c_msg["message"].split(' ')[1]
            if text_type != 'quote' and text_type != 'pun':
                return
        except Exception:
            self.twitch_send_message('Please specify a type to review.')
            return
        try:
            decision = c_msg["message"].split(' ')[2]
        except Exception:
            decision = ''
        if decision == 'start':
            if not self.review[text_type]:
                file_name = '{}_{}_review.txt'.format(self.channel, text_type)
                with open(file_name, 'a+') as data_file:
                    lines_read = data_file.readlines()
                lines = sum(1 for line in lines_read)
                if lines > 0:
                    for line in lines_read:
                        line = line.split('\n')[0]
                        self.review[text_type].append([line, 0])
                    self.twitch_send_message(self.review[text_type][0][0])
                else:
                    self.twitch_send_message('Nothing to review.')
            else:
                self.twitch_send_message("Review already started.")
        elif decision == 'approve':
            if self.review[text_type]:
                for text in self.review[text_type]:
                    if text[1] == 0:
                        text[1] = 1
                        self.text_review('review {} next'.format(text_type), 'Approved')
                        return
                self.text_review('review {} next'.format(text_type))
        elif decision == 'reject':
            if self.review[text_type]:
                for text in self.review[text_type]:
                    if text[1] == 0:
                        text[1] = 2
                        self.text_review('review {} next'.format(text_type), 'Rejected')
                        return
                self.text_review('review {} next'.format(text_type))
        elif decision == 'commit':
            if self.review[text_type]:
                file_name = '{}_{}_review.txt'.format(self.channel, text_type)
                for text in self.review[text_type]:
                    if text[1] == 0:
                        self.twitch_send_message('There are still more {}s to review, please finish reviewing first.'.format(text_type))
                        return
                with open(file_name, 'w') as data_file:
                    pass
                with open('{}_{}.txt'.format(self.channel, text_type), 'a') as data_file:
                    for line in self.review[text_type]:
                        if line[1] == 1:
                            data_file.write(line[0] + '\n')
                self.review[text_type] = []
                self.twitch_send_message('Approved {}s moved to the live file. Rejected quotes have been discarded.'.format(text_type))
        else:
            if self.review[text_type]:
                for text in self.review[text_type]:
                    if text[1] == 0:
                        if last_r == 'none':
                            self.twitch_send_message('Please use "!review {} (approve/reject)" for reviewing.'.format(text_type))
                            return
                        elif last_r == 'repeat':
                            self.twitch_send_message('New {} added, {}: '.format(text_type, text_type) + text[0])
                            return
                        else:
                            self.twitch_send_message(last_r + ", next quote: " + text[0])
                            return

                with open('{}_{}_review.txt'.format(self.channel, text_type), 'a+') as data_file:
                    new_text = data_file.readlines()
                new_sum = sum(1 for line in new_text)
                if new_sum != len(self.review[text_type]):
                    for i in new_text[len(self.review[text_type]):]:
                        self.review[text_type].append([i.split('\n')[0], 0])
                    self.text_review('review {} repeat'.format(text_type), 'repeat')
                    return
                if self.review[text_type]:
                    self.twitch_send_message('Please use "!review {} commit" to lock the changes in place.'.format(text_type))
                else:
                    self.twitch_send_message('Nothing {}s to review.'.format(text_type))

    def lister(self, c_msg, s_list):
        #Add user to blacklist or remove them from it
        #Blacklist will cause bot to completely ignore the blacklisted user
        user = c_msg["message"].split(' ')[-1]
        worked = False
        if s_list == 'black':
            self.blacklist.append(user)
            with open('blacklists/{}_blacklist.txt'.format(self.channel), 'a+') as data_file:
                data_file.write(user + '\n')
                worked = True
        elif s_list == 'white':
            if user in self.blacklist:
                self.blacklist.remove(user)
                with open('blacklists/{}_blacklist.txt'.format(self.channel), 'w') as data_file:
                    try:
                        data_file.write(self.blacklist)
                    except Exception:
                        pass
                worked = True
        if worked == True:
            self.twitch_send_message('{} has been {}listed'.format(user, s_list))

    def custom_command(self, c_msg):
        #Shitty custom command implementation,
        space_count = c_msg["message"].count(' ')
        if space_count == 0:
            command = c_msg["message"]
            param = ''
        else:
            command = c_msg["message"].split(' ')[0]
            param = c_msg["message"].split(' ')[-space_count]
        command = '!' + command
        if (command) not in self.custom_commands:
            return

        if self.custom_command_times[command]["admin"] and c_msg["tags"]["user_type"] not in self.elevated_user:
            return

        response = self.custom_command_times[command]["output"]
        response = response.replace("$sender", c_msg["sender"])
        response = response.replace("$param", param)

        self.twitch_send_message(response)
        self.custom_command_times[command]["last"] = int(time.time())

    def lol_masteries(self):
        #Pull the summoners active mastery page and adds up what trees they are in
        summoner_name = self.config_data['general']['summoner_name']
        name_url = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format(summoner_name, lol_api_key)
        name_data = self.api_caller(name_url)
        if name_data == False:
            return
        summoner_id = name_data[summoner_name]['id']
        mastery_url = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/{}/masteries?api_key={}'.format(summoner_id, lol_api_key)
        mastery_data = self.api_caller(mastery_url)
        if mastery_data == False:
            return
        for i in mastery_data[str(summoner_id)]['pages']:
            if i['current'] == True:
                active_set = i
                break
        masteries_used = {'offense' : 0, 'defense': 0, 'utility' : 0}
        for i in active_set['masteries']:
            if str(i['id'])[1] == '1':
                masteries_used['offense'] += i['rank']
            elif str(i['id'])[1] == '2':
                masteries_used['defense'] += i['rank']
            elif str(i['id'])[1] == '3':
                masteries_used['utility'] += i['rank']

        response = 'Page: {} | {}/{}/{}'.format(active_set['name'], masteries_used['offense'], masteries_used['defense'], masteries_used['utility'])
        self.twitch_send_message(response, '!masteries')

    def lol_runes(self):
        #Pulls the summoners active rune page, adds up all the values, and spits it out in chat
        #Most likely will not work for the double pen runes, never tested with those
        with open("runes.json",'r') as rune_file:
            runes_list = json.load(rune_file, encoding="utf-8")

        version_url = 'https://na.api.pvp.net/api/lol/static-data/na/v1.2/realm?api_key=' + lol_api_key
        version = self.api_caller(version_url)
        if version == False:
            return
        if version['n']['rune'] != runes_list['version']:
            url = 'http://ddragon.leagueoflegends.com/cdn/{}/data/en_US/rune.json'.format(version['n']['rune'])
            data = self.api_caller(url)
            with open('runes.json', 'w') as outfile:
                json.dump(data, outfile, sort_keys = True, indent = 4, ensure_ascii=False, encoding = 'utf-8')

        summoner_name = self.config_data['general']['summoner_name']
        name_url = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format(summoner_name, lol_api_key)
        name_data = self.api_caller(name_url)
        if name_data == False:
            return
        summoner_id = name_data[summoner_name]['id']

        rune_url = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/{}/runes?api_key={}'.format(summoner_id, lol_api_key)
        rune_data = self.api_caller(rune_url)
        if rune_data == False:
            return
        for i in rune_data[str(summoner_id)]['pages']:
            if i['current'] == True:
                active_page = i
                break

        runes_final = []
        runes_counted = {}
        for rune in active_page["slots"]:
            rune_id = str(rune['runeId'])
            if rune_id not in runes_counted:
                runes_counted[rune_id] = {'id' : rune_id, 'count' : 1, 'description' : runes_list['data'][rune_id]['description'], 'stats' : runes_list['data'][rune_id]['stats'].keys()}
            else:
                runes_counted[rune_id]['count'] += 1

        for k, v in runes_counted.iteritems():
            if 'per level' in v['description']:
                string = ''
                string += v['description'].split('(')[1].split(' ')[0]
                string += ' ' + ' '.join(v['description'].split(' ')[1:-1])
                string = string.split('(')[0]
                string = re.sub('per level', 'at level 18', string)
                runes_counted[k]['description'] = string
            if re.search('[+-](\d+\.\d+)', v['description']):
                data = re.findall('[+-](\d+\.\d+)', v['description'])[0]
                value = float(data) * v['count']
                runes_counted[k]['description'] = v['description'][0] + re.sub('[+-](\d+\.\d+)', str(value), v['description'])
                runes_counted[k]['value'] = value
            else:
                data = re.findall('[+-](\d+)', v['description'])
                value = int(data[0]) * v['count']
                runes_counted[k]['description'] = v['description'][0] + re.sub('[+-](\d+)', str(value), v['description'])
                runes_counted[k]['value'] = value

        for k, v in runes_counted.items():
            for k2, v2 in runes_counted.items():
                if k == k2:
                    continue
                if v['stats'][0] == v2['stats'][0]:
                    try:
                        runes_counted[k]['value'] = v['value'] + v2 ['value']
                        del runes_counted[k2]
                    except Exception:
                        pass

        for k, v in runes_counted.iteritems():
            if re.search('[+-](\d+\.\d+)', v['description']):
                text = v['description'][0] + re.sub('[+-](\d+\.\d+)', str(v['value']), v['description'])
                runes_final.append(text)
            else:
                text = v['description'][0] + re.sub('[+-](\d+)', str(v['value']), v['description'])
                runes_final.append(text)

        response = 'Page: {} | Stats: '.format(active_page['name'])
        response += ' | '.join(runes_final)
        self.twitch_send_message(response, '!runes')

    def get_time_objects(self):
        current_object = datetime.datetime.now(pytz.utc)
        live_object = isodate.parse_datetime(self.time_start)
        return current_object, live_object

    def uptime(self):
        if self.time_start != None:
            current_object, live_object = self.get_time_objects()
            total_live_object = current_object - live_object
            self.twitch_send_message("The current stream has been live for " + str(total_live_object)[:-7], '!uptime')
        else:
            self.twitch_send_message("The stream is not currently live. If you just went live wait up to one minute for Twitch to register it.", '!uptime')

    def highlight(self, c_msg):
        if self.time_start != None:
            current_object, live_object = self.get_time_objects()
            time_to_highlight = current_object - live_object
            self.to_highlight.append({'time' : str(time_to_highlight)[:-7], 'desc' : c_msg["message"].split('highlight')[-1]})
            self.twitch_send_message("Current time added to the highlight queue. Use !show_highlight to view them.")
        else:
            self.twitch_send_message("Please use the command when the stream is live.")

    def show_highlight(self):
        if self.to_highlight:
            msg = "Things you need to highlight: "
            for i in self.to_highlight:
                msg += i['desc'] + " @ " + i['time'] + ", "
            self.twitch_send_message(msg[:-2])
            self.to_highlight = []
        else:
            msg = "Highlight queue empty, use '!highlight (description)' when the stream is live."
            self.twitch_send_message(msg)

    def eight_ball(self, c_msg):
        question = c_msg["message"].split(' ')[1:]
        if not question:
            self.twitch_send_message("Magic 8ball says: Ask me a question")
            return
        answers = [
            "It is certain",
            "It is decidedly so",
            "Without a doubt",
            "Yes definitely",
            "You may rely on it",
            "As I see it, yes",
            "Most likely",
            "Outlook good",
            "Yes",
            "Signs point to yes",
            "Reply hazy try again",
            "Ask again later",
            "Better not tell you now",
            "Cannot predict now",
            "Concentrate and ask again",
            "Don't count on it",
            "My reply is no",
            "My sources say no",
            "Outlook not so good",
            "Very doubtful"
            ]
        response = "Magic 8-ball says: {}".format(random.choice(answers))
        self.twitch_send_message(response, "!8ball")

    def sub_msg(self, c_msg):
        msg_split = c_msg.split(' ')
        if len(msg_split) == 3:
            msg = self.config_data["sub_message_text"]
            msg = msg.replace("$subscriber", msg_split[0])
        else:
            msg = self.config_data["sub_message_resub"]
            msg = msg.replace("$duration", "{} {}".format(msg_split[3], msg_split[4]))
            msg = msg.replace("$subscriber", msg_split[0])
        self.twitch_send_message(msg)


    def twitch_run(self):
        #Main loop for running the bot
        self.twitch_connect()   #Connect to IRC
        self.twitch_commands()  #Get all the commands in order

        while self.running:

            try:
                message = self.irc.recv(4096)
            except socket.timeout:
                print self.channel + ' timed out.'
                if self.running:
                    self.socket_error_restart()

            if message == "":
                if self.running:
                    print self.channel + ' returned empty string.'
                    self.socket_error_restart()
            elif message.startswith('PING'):
                self.irc.raw(message.replace("PING", "PONG").strip())

            try:
                message = message.strip()
                msg_parts = message.split(' ')
                if message.startswith(':'):
                    action = msg_parts[1]
                    msg_parts.insert(0, '')
                elif message.startswith('@'):
                    action = msg_parts[2]
                else:
                    action = ''
            except Exception:
                traceback.print_exc(limit=2)
                continue

            if action == 'PRIVMSG':
                self.messages_received += 1
                c_msg = {}
                if msg_parts[0]:
                    c_msg["tags"] = dict(item.split('=') for item in msg_parts[0][1:].split(';'))
                else:
                    c_msg["tags"] = {"color": "", "emotes": {}, "subscriber": 0, "turbo": 0, "user_type": ""}
                c_msg["sender"] = msg_parts[1][1:].split('!')[0]
                c_msg["action"] = msg_parts[2]
                c_msg["channel"] = msg_parts[3]
                c_msg["message"] = ' '.join(msg_parts[4:])[1:]

                if c_msg["sender"] in self.blacklist:
                    continue

                if self.__DB:
                    print u"[{}] #{} {}: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.channel, c_msg["sender"], c_msg["message"]).encode("utf-8")

                # if self.__DB:
                #     print datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] #{} {}: {}".decode("utf-8").format(self.channel, c_msg["sender"], c_msg["message"]))

                #Sub Message
                if c_msg["sender"] == 'twitchnotify':
                    if self.config_data["sub_message_active"]:
                        self.sub_msg(c_msg)

                #Link osu maps
                if c_msg["message"].find('osu.ppy.sh/b/') != -1 or c_msg["message"].find('osu.ppy.sh/s/') != -1:
                    if self.game == 'osu!':
                        if self.config_data["osu_link"]:
                            self.osu_link(c_msg)

                #Link youtube info
                if self.config_data["youtube_link"]:
                    self.youtube_video_check(c_msg)

                #Toobou trigger check
                try:
                    if c_msg["message"].lower().find(self.t_trig.lower()) != -1:
                        if 'toobou' in self.command_times and self.config_data["toobou_output"] != "":
                            if self.time_check('toobou'):
                                self.twitch_send_message(self.config_data["toobou_output"])
                                self.command_times['toobou']['last'] = int(time.time())
                except Exception:
                    pass

                if c_msg["message"].startswith('!'):
                    #Dirty work around to allow text to have more !'s in them
                    c_msg["message"] = c_msg["message"].split('!', 1)[1]

                    #All commands go here

                    if self.custom_commands:
                        self.custom_command(c_msg)

                    if c_msg["message"].startswith('blacklist ') and c_msg["sender"] == self.channel:
                        self.lister(c_msg, 'black')

                    elif c_msg["message"].startswith('whitelist ') and c_msg["sender"] == self.channel:
                        self.lister(c_msg, 'white')

                    elif c_msg["message"].startswith("pb"):
                        if self.command_check(c_msg, "!pb"):
                            self.pb_retrieve(c_msg)

                    elif c_msg["message"].startswith('wr'):
                        if self.command_check(c_msg, '!wr'):
                            self.wr_retrieve(c_msg)

                    elif c_msg["message"].startswith('leaderboard'):
                        if self.game != '':
                            if self.command_check(c_msg, '!leaderboard'):
                                self.leaderboard_retrieve()

                    elif c_msg["message"].startswith("splits"):
                        if self.command_check(c_msg, '!splits'):
                            self.splits_check(c_msg)

                    elif c_msg["message"].startswith('addquote'):
                        if self.command_check(c_msg, '!addquote'):
                            self.add_text(c_msg, "quote")

                    elif c_msg["message"] == 'quote':
                        if self.command_check(c_msg, '!quote'):
                            self.text_retrieve('quote')

                    elif c_msg["message"].startswith('addpun'):
                        if self.command_check(c_msg, '!addpun'):
                            self.add_text(c_msg, "pun")

                    elif c_msg["message"] == 'pun':
                        if self.command_check(c_msg, '!pun'):
                            self.text_retrieve('pun')

                    elif c_msg["message"] == 'rank':
                        if self.game == 'osu!':
                            if self.command_check(c_msg, '!rank'):
                                self.osu_api_user()

                    elif c_msg["message"] == 'song':
                        if self.game == 'osu!':
                            if self.command_check(c_msg, '!song'):
                                self.osu_song_display()

                    elif c_msg["message"] == 'race':
                        if 'race' in self.title or 'racing' in self.title:
                            if self.command_check(c_msg, '!race'):
                                self.srl_race_retrieve()

                    elif c_msg["message"].startswith('createvote '):
                        if self.config_data["voting_mods"] and (c_msg["tags"]["user_type"] in self.elevated_user or c_msg["sender"] == self.channel):
                            self.create_vote(c_msg)

                    elif c_msg["message"] == 'endvote':
                        if self.config_data["voting_mods"] and (c_msg["tags"]["user_type"] in self.elevated_user or c_msg["sender"] == self.channel):
                            self.end_vote()

                    elif c_msg["message"].startswith('vote '):
                        if self.config_data["voting_active"]:
                            self.vote(c_msg)

                    elif c_msg["message"] == 'checkvotes':
                        if self.config_data["voting_active"]:
                            self.check_votes()

                    elif c_msg["message"].startswith('review') and c_msg["sender"] == self.channel:
                        self.text_review(c_msg)

                    elif c_msg["message"] == 'runes':
                        if self.game == 'league of legends':
                            if self.command_check(c_msg, '!runes'):
                                self.lol_runes()

                    elif c_msg["message"] == "masteries":
                        if self.game == 'league of legends':
                            if self.command_check(c_msg, '!masteries'):
                                self.lol_masteries()

                    elif c_msg["message"] == "uptime":
                        if self.command_check(c_msg, '!uptime'):
                            self.uptime()

                    elif c_msg["message"].startswith('highlight'):
                        if self.command_check(c_msg, "!highlight"):
                            self.highlight(c_msg)

                    elif c_msg["message"].startswith("8ball"):
                        if self.command_check(c_msg, "!8ball"):
                            self.eight_ball(c_msg)

                    elif c_msg["message"] == "show_highlight":
                        if c_msg["sender"] == self.channel or c_msg["sender"] in SUPER_USER:
                            self.show_highlight()

                    elif c_msg["message"] == "commands":
                        if self.command_check(c_msg, "!commands"):
                            self.live_commands()

                    elif c_msg["message"] == "bot_info":
                        if self.command_check(c_msg, "!bot_info"):
                            msg = "Powered by SaltyBot, for a full list of command check out the github repo (http://bombch.us/z3x) or to get it in your channel go here http://bombch.us/z3y"
                            self.twitch_send_message(msg, "!bot_info")

                    elif c_msg["message"] == "restart" and c_msg["sender"] in SUPER_USER:
                        if self.__DB:
                            print "{} is restarting, called by {}".format(self.channel + ' ' + self.twitch_nick, c_msg["sender"])
                        self.admin(RESTART)
                        self.twitch_send_message("Restarting the bot.")
                        break

                    elif c_msg["message"] == "check":
                        if c_msg["sender"] in SUPER_USER:
                            self.admin(CHECK)

                    elif c_msg["message"] == "crash":
                        if c_msg["sender"] in SUPER_USER:
                            self.running = False

                    #Commands end here

            #Check the social down here, so that even if ping happens social can go off if the minimum time/messages are met but no one is talking
            if self.config_data["social_active"] and self.stream_online:
                if self.messages_received >= (self.command_times['social']['messages'] + self.command_times['social']['messages_last']):
                    if int(time.time()) >= ((self.command_times['social']['time'] * 60) + self.command_times['social']['time_last']):
                        self.twitch_send_message(self.social_text)
                        self.command_times['social']['time_last'] = int(time.time())
                        self.command_times['social']['messages_last'] = self.messages_received

        print "thread stoped"
    #@@ ADMIN FUNCTIONS @@#

    def socket_error_restart(self):
        self.irc.disconnect()
        self.irc = irc.IRC("irc.twitch.tv", 443, self.twitch_nick, self.twitch_oauth)
        self.twitch_connect()
        return

    def admin(self, call='<test>'):
        if call == RESTART:
            interface.put([call, self])
            if self.__DB:
                print 'bot id {}'.format(self)

        else:
            interface.put([call,self])

    def stop(self):
        self.irc.disconnect()

#@@BOT END@@#

def osu_send_message(osu_irc_pass, osu_nick, msg, sender):
    #Send the message through IRC to the person playing osu
    full_msg = "{}: {}".format(sender, msg)
    irc = irc.IRC("irc.ppy.sh", 6667, osu_irc_nick, osu_irc_pass)
    irc.create()
    irc.connect()
    irc.privmsg(osu_nick, full_msg)
    irc.disconnect()

def twitch_info_grab(bots):
    #Grab all the people using the bots data in one call using stream objects

    channels = bots.keys()
    new_info = {}
    for i in channels:
        new_info[i] = {"game" : '', "title" : '', "live" : None, "online_status": False}
    url = 'https://api.twitch.tv/kraken/streams?channel=' + ','.join(channels)
    headers = {'Accept' : 'application/vnd.twitchtv.v3+json'}
    try:
        data = requests.get(url, headers = headers)
        if data.status_code == 200:
            data_decode = data.json()
            if not data_decode['streams']:
                for k, v in new_info.iteritems():
                    bots[k].twitch_info(**v)
                return
            for i in data_decode['streams']:
                new_info[i['channel']['name']] = {"game" : i['channel']['game'],
                                                "title" : i['channel']['status'],
                                                "live" : i["created_at"],
                                                "online_status": True}
            for k, v in new_info.iteritems():
                bots[k].twitch_info(**v)

        else:
            pass
    except Exception:
        traceback.print_exc(limit=2)

def restart_bot(bot_name, bot_config, bot_dict):
    current_irc = bot_dict[bot_name].irc
    del bot_dict[bot_name]
    bot_dict[bot_name] = SaltyBot(bot_config[bot_name], debuging, irc_obj=current_irc)
    bot_dict[bot_name].start()

def update_bot(bot_name, bot_config, bot_dict):
    try:
        if bot_config["active"]:
            if bot_config["bot_nick"] == bot_dict[bot_name].twitch_nick:
                bot_dict[bot_name].config_data = bot_config
                bot_dict[bot_name].commands = []
                bot_dict[bot_name].admin_commands = []
                bot_dict[bot_name].custom_commands = []
                bot_dict[bot_name].twitch_commands()
            else:
                bot_dict[bot_name].running = False
                bot_dict[bot_name].stop()
                del bot_dict[bot_name]
                bot_dict[bot_name] = SaltyBot(bot_config, debuging)
                bot_dict[bot_name].start()
                print "Name changed for {}".format(bot_name)
            print "Updated bot for {}".format(bot_name)
        else:
            bot_dict[bot_name].running = False
            bot_dict[bot_name].stop()
            del bot_dict[bot_name]
            print "Deleted bot for {}".format(bot_name)
    except KeyError:
        if bot_config["active"]:
            bot_dict[bot_name] = SaltyBot(bot_config, debuging)
            bot_dict[bot_name].start()
            print "Created bot for {}".format(bot_name)

def automated_main_loop(bot_dict, config_dict):
    time_to_check_twitch = 0
    next_buffer_clear = 0

    while True:
        try:
            register = interface.get(False) #returns [type of call, bot id that called it] therefore TYPE, DATA

            if register:
                if register[TYPE] == RESTART:
                    restart_bot(register[DATA].channel, config_dict, bot_dict)
                elif register[TYPE] == CHECK:
                    for bot_name,bot_inst in bot_dict.items():
                        print bot_name + ': ' + bot_inst.thread
                elif register[TYPE] == UPDATE:
                    user = dict(register[DATA]).keys()[0]
                    update_bot(user, register[DATA][user], bot_dict)
                    config_dict[user] = register[DATA][user]
                register = None

        except Q.Empty:
            pass
        except Exception:
            traceback.print_exc(limit=2)

        for bot_name, bot_inst in bot_dict.items():
            try:
                if not bot_inst.thread.isAlive():
                    if debuging == True:
                        print '#' + bot_name + ' Had to restart'
                    restart_bot(bot_inst.channel, config_dict, bot_dict)
                    bot_dict[bot_name].twitch_send_message("An error has caused the bot to crash, if this problem persists or is replicatable please send a message to bomb_mask")
            except AttributeError:
                continue

        current_time = int(time.time())

        if next_buffer_clear < current_time:
            for bot_name, bot_inst in bot_dict.items():
                bot_inst.clear_limiter()
            next_buffer_clear = int(time.time()) + 30

        if time_to_check_twitch < current_time:
            twitch_info_grab(bot_dict)
            time_to_check_twitch = int(time.time()) + 60

def update_listen(web_inst):
    while True:
        try:
            user_to_update = web_inst.main_listen()
        except ValueError:
            print "Was given wrong secret key"
            continue
        try:
            user = json.loads(user_to_update)
        except ValueError:
            traceback.print_exc(limit=2)
            continue
        try:
            new_info = web_inst.update_retrieve(user["user_id"])
        except Exception:
            traceback.print_exc(limit=2)
            continue
        interface.put([UPDATE, new_info])
        print "New info in register"

def main():

    bot_dict = {} #Bot instances go in here

    online_info = SaltyListener.WebRetrieve(development, db_url, web_listen_ip, web_listen_port, web_secret)
    channels_dict = online_info.initial_retrieve() #All channels go in here from the JSON file

    for channel_name, channel_data in channels_dict.items(): #Start bots
        # Create bot and put it by name into a dictionary

        bot_dict[channel_name] = SaltyBot(channel_data, debuging)

        # Look up bot and start the thread
        bot_dict[channel_name].start()

        # Wait for twitch limit
        time.sleep(1)

    otherT = threading.Thread(target=automated_main_loop, args=(bot_dict, channels_dict))
    otherT.setDaemon(True)
    otherT.start()

    listen_thread = threading.Thread(target=update_listen, args=(online_info,))
    listen_thread.setDaemon(True)
    listen_thread.start()

    while True:
        command = raw_input("> ")
        if command.startswith("/brcs"):
            for inst in bot_dict.values():
                inst.twitch_send_message("[Broadcast message]: "+(' '.join(command.split(' ')[1:])))

        if command.startswith("/stop"):
            for inst in bot_dict.values():
                inst.stop()
            sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Shut-down initiated..."
