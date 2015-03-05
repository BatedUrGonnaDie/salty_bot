#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os
import Queue as Q
import random
import re
import socket
import sys
import threading
import time
import urlparse

import requests
import psycopg2
import psycopg2.extras

#import salty_config

debuging = True
Config_file_name = 'config.json'

RESTART = "<restart>"
STOP = "<stop program>"
CHECK = "<check threads>"

TYPE = 0
DATA = 1

interface = Q.Queue()

#Set up all the global variables
with open('general_config.json', 'r') as data_file:
    general_config = json.load(data_file, encoding = 'utf-8')

lol_api_key = general_config['general_info']['lol_api_key']
youtube_api_key = general_config['general_info']['youtube_api_key']
osu_api_key = general_config['general_info']['osu']['osu_api_key']
osu_irc_nick = general_config['general_info']['osu']['osu_irc_nick']
osu_irc_pass = general_config['general_info']['osu']['osu_irc_pass']
db_url = general_config['general_info']['db_url']
#super users are used for bot breaking commands and beta commands
SUPER_USER = general_config['general_info']['super_users']

class SaltyBot:

    running = True
    messages_received = 0
    message_limit = 100
    rate_limit = 0

    def __init__(self, config_data, debug = False):
        self.__DB = debug
        self.session = config_data["session"]
        self.user_id = config_data["id"]
        self.config_data = config_data
        self.irc = socket.socket()
        self.twitch_host = "irc.twitch.tv"
        self.port = 443
        self.twitch_nick = config_data["bot_nick"]
        self.twitch_oauth = config_data["bot_oauth"]
        if not self.twitch_oauth.startswith("oauth:"):
            self.twitch_oauth = "oauth:" + self.twitch_oauth
        self.channel = config_data["twitch_name"]
        self.game = ''
        self.title = ''
        self.time_start = ''
        self.commands = []
        self.admin_commands = []
        self.custom_commands = []
        self.blacklist = []
        self.t_trig = None
        with open('{}_blacklist.txt'.format(self.channel), 'a+') as data_file:
            blacklist = data_file.readlines()
        for i in blacklist:
            self.blacklist.append(i.split('\n')[0])
        self.command_times = {}
        self.custom_command_times = {}
        self.elevated_user = ["staff", "admin", "global_mod", "mod"]

    def start(self):
        self.thread = threading.Thread(target=self.twitch_run)
        self.thread.setDaemon(True)
        self.thread.start()

        return self.thread

    def twitch_info(self, game, title, live):
        #Game and title need to be a string to work
        self.game = game.lower()
        self.game_normal = game
        self.title = title.lower()
        self.time_start = live

    def twitch_connect(self):
        #Connect to Twitch IRC
        if self.__DB:
            print "Joining {} as {}.\n".format(self.channel,self.twitch_nick)
        try:
            #If it fails to conenct try again in 60 seconds
            self.irc.settimeout(600)
            self.irc.connect((self.twitch_host, self.port))
        except Exception, e:
            print '{} failed to connect.'.format(self.channel)
            print e
            time.sleep(60)
            self.twitch_connect()

        self.irc.sendall('PASS {}\r\n'.format(self.twitch_oauth))
        self.irc.sendall('NICK {}\r\n'.format(self.twitch_nick))
        initial_msg = self.irc.recv(4096)
        self.irc.sendall("CAP REQ :twitch.tv/tags twitch.tv/commands\r\n")
        self.irc.recv(1024)
        self.irc.sendall('JOIN #{}\r\n'.format(self.channel))

    def twitch_commands(self):
        #Set up all the limits, if its admin, if its on, quote and pun stuff, and anything else that needs setting up for a command
        self.command_times["!bot_info"] = {"last": 0, "limit": 30}
        self.commands.append("!bot_info")

        for i in self.config_data["commands"]:
            if i["on"]:
                curr_com = "!" + i["name"]
                if i["admin"]:
                    self.admin_commands.append(curr_com)
                else:
                    self.commands.append(curr_com)
                self.command_times[curr_com] = {"last": 0, "limit": i["limit"]}

        if '!vote' in self.commands:
            self.votes = {}

        if '!highlight' in self.commands:
            self.to_highlight = []

        if '!quote' in self.commands or '!pun' in self.commands:
            self.review = {}
            self.last_text = {}
            if '!quote' in self.commands:
                self.review['quote'] = []
                self.last_text['quote'] = ''
            if '!pun' in self.commands:
                self.review['pun'] = []
                self.last_text['pun'] = ''

        if self.config_data["social_active"]:
            self.command_times["social"] = {"time_last": int(time.time()),
                                            "messages": self.config_data["social_messages"],
                                            "messages_last": self.messages_received,
                                            "time": self.config_data["social_time"]}
            self.social_text = self.config_data["social_output"]

        if self.config_data["toobou_active"]:
            self.t_trig = self.config_data["toobou_trigger"]
            self.command_times["toobou"] = {"trigger": self.t_trig,
                                            "last": 0,
                                            "limit": self.config_data["toobou_limit"]}

        for i in self.config_data["custom_commands"]:
            if i["on"]:
                self.custom_commands.append("!{}".format(i["trigger"]))
                self.custom_command_times["!{}".format(i["trigger"])] = {"last": 0, "limit": i["limit"], "output": i["output"], "admin": i["admin"]}

    def live_commands(self):
        #Remove any commands that would not currently work when !commands is used
        active_commands = list(self.commands) + list(self.custom_commands)

        if not self.time_start:
            try:
                active_commands.remove('!uptime')
            except:
                pass
        try:
            if not self.votes:
                try:
                    active_commands.remove("!vote")
                except:
                    pass
        except AttributeError, e:
            pass

        if self.game == '':
            try:
                active_commands.remove('!leaderboard')
            except:
                pass
        
        if self.game != 'osu!':
            try:
                active_commands.remove('!rank')
            except:
                pass
            try:
                active_commands.remove('!song')
            except:
                pass

        if self.game != 'league of legends':
            try:
                active_commands.remove('!runes')
            except:
                pass
            try:
                active_commands.remove('!masteries')
            except:
                pass
        
        if 'race' not in self.title and 'racing' not in self.title:
            try:
                active_commands.remove('!race')
            except:
                pass

        command_string = ', '.join(active_commands)
        if command_string == '!commands':
            self.twitch_send_message('There are no current active commands.', '!commands')
        else:
            self.twitch_send_message(command_string, '!commands')

    def clear_limiter(self):
        self.rate_limit = 0

    def twitch_send_message(self, response, command = None):

        #Sending any message to chat goes through this function
        try:
            response = response.encode('utf-8')
        except:
            pass
        if response.startswith('/me') or response.startswith('.me'):
            #Grant exception for /me because it can't do any harm
            pass
        elif response.startswith('.') or response.startswith('/'):
            #Prevent people from issuing server commands since bot is usually mod (aka /ban)
            response = "Please stop trying to abuse me BibleThump"
            command = ''
        to_send = 'PRIVMSG #{} :{}\r\n'.format(self.channel, response)
        if self.rate_limit < self.message_limit:
            self.irc.sendall(to_send)
            self.rate_limit += 1
        else: 
            return

        if self.__DB == True: 
            try:
                db_message = '#' + self.channel + ' ' + self.twitch_nick + ": " + response.decode('utf-8')
                db_message = db_message.encode('utf-8')
                print datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ') + db_message
            except:
                print("Message contained unicode, could not display in terminal\n\n")

        if command:
            #Update when the command was last used for rate limiting
            self.command_times[command]['last'] = int(time.time())

    def command_check(self, c_msg, command):
        #Finds if the user can use said command, and then if the command is off cooldown
        #Will only return True if it's off cooldown and the user has the priviledges for the command
        if command in self.commands:
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
        except Exception, e:
            print e
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
        osu_nick = self.config_data["osu_nick"]
        url = 'https://leagueofnewbs.com/api/user/{}/songs'.format(self.channel)
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
        if s < 10:
            s = '0' + str(s)
        if m < 10:
            m = '0' + str(m)
        time = '{}:{}:{}'.format(int(h), m, s)
        if time.endswith(".0"):
            time = time[:-2]
        if time.startswith("0:"):
            time = time[2:]
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
            response = "I'm sorry, but this category does not exist on speedrun.com"
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
        try:
            url = "http://www.speedrun.com/api_records.php?user={}".format(msg_split[1])
            user_name = msg_split[1]
            try:
                url += "&game=" + msg_split[2]
                try:
                    msg_split[3]
                except IndexError, e:
                    if self.title != '':
                        infer_category = True
                    else:
                        self.twitch_send_message("Please specify a category to look up.")
                        return
            except IndexError, e:
                if self.game != '':
                    url += "&game=" + self.game
                else:
                    self.twitch_send_message("Please specify a game shortcode to look up on speedrun.com")
                    return
        except IndexError, e:
            if self.game != '':
                url = "http://speedrun.com/api_records.php?user={}&game={}".format(self.channel, self.game)
                user_name = self.channel
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
        except TypeError, e:
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
            except NameError, e:
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

        try:
            url = "http://www.speedrun.com/api_records.php?game=" + msg_split[1]
            try:
                msg_split[2]
            except IndexError:
                self.twitch_send_message("Please provide a category to search for.", '!wr')
                return
        except IndexError:
            if self.game != '':
                url = "http://www.speedrun.com/api_records.php?game=" + self.game
            else:
                self.twitch_send_message("Please either provide a game and category or wait for the streamer to go live.", '!wr')
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
        wr_time = self.format_sr_time(cat_record['time'])
        msg = "The current world record for {} {} is {} by {}.".format(sr_game, active_cat, wr_time, cat_record['player'])
        if cat_record['video']:
            msg += "  The video can be found here: " + cat_record['video']
        self.twitch_send_message(msg, '!wr')

    def leaderboard_retrieve(self):
        #Retrieve leaderboard for game as set on Twitch
        game_no_spec = re.sub(' ', '_', self.game_normal)
        game_no_spec = re.sub("[:]", '', game_no_spec)
        url = 'http://speedrun.com/' + game_no_spec
        self.twitch_send_message(url, '!leaderboard')

    def splits_check(self):
        #Get user JSON object from splits.io, find the categories, find the fastest run for said category, and then link
        #it in chat for people to see the time/download
        url = "https://splits.io/api/v2/users?name=" + self.channel
        user_id = self.api_caller(url)
        if user_id == False:
            self.twitch_send_message("I'm sorry, I could not retrieve the user id from splits.io")
            return
        user_id = user_id[0]['id']
        url = "https://splits.io/api/v2/runs?user_id=" + user_id
        user = self.api_caller(url)
        if not user:
            self.twitch_send_message("I'm sorry, I could not retrieve the users runs from splits.io")
            return

        user = user['runs']
        if len(user) == 0:
            self.twitch_send_message("I'm sorry, but {} has no runs on splits.io".format(self.channel), "!splits")
            return
        categories_in_title = []
        category_position = {}

        for i in user:
            if i['game']['name'] == None or i['category']['name'] == None:
                continue

            if i['game']['name'].lower() == self.game:
                if i['category']['name'].lower() in self.title:
                    categories_in_title.append(i['category']['name'].lower())

        if len(categories_in_title) == 0:
            self.twitch_send_message("I'm sorry, but I could not find any runs matching the categories in the title.", '!splits')
            return
        elif len(categories_in_title) == 1:
            current_cat = categories_in_title[0]
        elif len(categories_in_title) > 1:
            for i in range(len(categories_in_title)):
                for j in range(i + 1, len(categories_in_title)):
                    if categories_in_title[i] == categories_in_title[j]:
                        del categories_in_title[j]
                
                try:
                    category_position[i] = self.title.find(categories_in_title[i])
                except:
                    pass
            if len(categories_in_title) > 1:
                current_cat = min(category_position, key = category_position.get)
            else:
                current_cat = categories_in_title[0]
        else:
            print current_cat
            current_cat = categories_in_title[0]

        best_time = 0

        for i in user:
            if i['game']['name'] == None or i['category']['name'] == None:
                continue
            if i['game']['name'].lower() == self.game and i['category']['name'].lower() == current_cat:
                if best_time == 0:
                    best_time = i['time']
                    splits = i
                if i['time'] < best_time:
                    splits = i

        if best_time == 0:
            return

        time = self.format_sr_time(splits['time'])
        link = 'https://splits.io/{}'.format(splits['path'])
        response = 'Splits with a time of {} {}'.format(time, link)
        self.twitch_send_message(response, '!splits')

    def add_text(self, c_msg, text_type):
        #Add a pun or quote to the review file
        text = c_msg["message"][(len(text_type) + 4):]
        text = text.strip()

        if text == 'add{}'.format(text_type) or text == 'add{} '.format(text_type):
            self.twitch_send_message('Please input a {}.'.format(text_type))
        else:
            url = "https://leagueofnewbs.com/api/user/{}/{}s".format(self.channel, text_type)
            data = {"reviewed": 1 if c_msg["sender"] == self.channel else 0,
                    "text": text,
                    "user_id": self.channel}
            cookies = {"session": self.session}
            
            success = requests.post(url, data=data, cookies=cookies)
            try:
                success.raise_for_status()
                reviewed = "to the database" if c_msg["sender"] == self.channel else "for review"
                response = "Your {} has been added {}.".format(text_type, reviewed)
            except Exception, e:
                print e
                response = "I had problems adding this to the database."
            self.twitch_send_message(response, "!add" + text_type)

    def text_retrieve(self, text_type):
        #Pull a random pun/quote from the database
        #Will not pull the same one twice in a row
        text_type_plural = text_type + 's'
        url = "https://leagueofnewbs.com/api/user/{}/{}?limit=2".format(self.channel, text_type_plural)
        text_lines = self.api_caller(url)
        if text_lines:
            if text_lines[text_type_plural][0]["text"] != self.last_text[text_type]:
                response = text_lines[text_type_plural][0]["text"]
            else:
                response = text_lines[text_type_plural][1]["text"]
        else:
            response = "There was a problem retrieving {}.".format(text_type_plural)

        self.twitch_send_message(response, '!' + text_type)
        self.last_text[text_type] = response

    def srl_race_retrieve(self):
        #Goes through all races, finds the race the user is in, gathers all other users in the race, prints the game, the 
        #category people are racing, the time racebot has, and either a multitwitch link or a SRL race room link
        self.srl_nick = self.config_data["srl_nick"]
        url = 'http://api.speedrunslive.com/races'
        data_decode = self.api_caller(url)
        if data_decode == False:
            return
        data_races = data_decode['races']
        srl_race_entrants = []
        for i in data_races:
            for races in i['entrants']:
                if self.srl_nick in races:
                    race_channel = i
                    for values in race_channel['entrants'].values():
                        if values['statetext'] == 'Ready' or values['statetext'] == 'Entered':
                            if values['twitch'] != '':
                                srl_race_entrants.append(values['twitch'].lower())
                    user = i['entrants'][self.srl_nick]['twitch']
                    user_place = race_channel['entrants'][self.srl_nick]['place']
                    user_time = race_channel['entrants'][self.srl_nick]['time']
                    srl_race_game = race_channel['game']['name']
                    srl_race_category = race_channel['goal']
                    srl_race_id = '#srl-' + race_channel['id']
                    srl_race_status = race_channel['statetext']
                    srl_race_time = race_channel['time']
                    srl_race_link = 'http://www.speedrunslive.com/race/?id={}'.format(race_channel['id'])
                    srl_live_entrants = []
                    live_decoded = self.api_caller('https://api.twitch.tv/kraken/streams?channel=' + ','.join(srl_race_entrants))
                    for j in live_decoded['streams']:
                        srl_live_entrants.append(j['channel']['name'])
                    multitwitch_link = 'www.multitwitch.tv/'
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
                        for j in srl_live_entrants:
                            multitwitch_link += j + '/'
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
                duration = (data_items[0]['contentDetails']['duration'])[2:-1]
                duration_list = re.split("[HMS]", duration)
                if len(duration_list) == 1:
                    duration_string = "0:" + duration_list[0]
                else:
                    duration_string = ':'.join(duration_list)

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
        except:
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
        except:
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

    def check_votes(self, c_msg):
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
        except:
            self.twitch_send_message('Please specify a type to review.')
            return
        try:
            decision = c_msg["message"].split(' ')[2]
        except:
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
            with open('{}_blacklist.txt'.format(self.channel), 'a+') as data_file:
                data_file.write(user + '\n')
                worked = True
        elif s_list == 'white':
            if user in self.blacklist:
                self.blacklist.remove(user)
                with open('{}_blacklist.txt'.format(self.channel), 'w') as data_file:
                    try:
                        data_file.write(self.blacklist)
                    except:
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
        runes_stats = runes_list['basic']['stats']
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
                    except:
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
        current_time = time.gmtime()
        current_object = datetime.datetime(current_time[0], current_time[1], current_time[2], current_time[3], current_time[4], current_time[5])

        time_live_split = re.split("(\d{4}?)-(\d{2}?)-(\d{2}?)T(\d{2}?):(\d{2}?):(\d{2}?)Z", self.time_start)[1:-1]
        for i, s in enumerate(time_live_split):
            time_live_split[i] = int(s)
        live_object = datetime.datetime(time_live_split[0], time_live_split[1], time_live_split[2], time_live_split[3], time_live_split[4], time_live_split[5])
        
        return current_object, live_object

    def uptime(self):
        if self.time_start != None:
            current_object, live_object = self.get_time_objects()
            total_live_object = current_object - live_object
            self.twitch_send_message("The current stream has been live for " + str(total_live_object), '!uptime')
        else:
            self.twitch_send_message("The stream is not currently live.", '!uptime')

    def highlight(self, c_msg):
        if self.time_start != None:
            current_object, live_object = self.get_time_objects()
            time_to_highlight = current_object - live_object
            self.to_highlight.append({'time' : str(time_to_highlight), 'desc' : c_msg["message"].split('highlight')[-1]})
            self.twitch_send_message("Current time added to the highlight queue. Use !show_highlight to view them.")
        else:
            self.twitch_send_message("Please use the command when the stream is live.")

    def show_highlight(self):
        msg = "Things you need to highlight: "
        for i in self.to_highlight:
            msg += i['desc'] + " @ " + i['time'] + ", "
        self.twitch_send_message(msg[:-2])
        self.to_highlight = []

    def sub_msg(self, c_msg):
        pass

    def twitch_run(self):
        #Main loop for running the bot
        self.twitch_connect()   #Connect to IRC
        self.twitch_commands()  #Get all the commands in order

        while self.running:

            try:
                message = self.irc.recv(4096)
            except socket.timeout:
                print self.channel + ' timed out.'
                self.socket_error_restart()

            if message == "":
                print self.channel + ' returned empty string.'
                self.socket_error_restart()

            if message.startswith('PING'):
                self.irc.sendall(message.replace("PING", "PONG"))

            try:
                message = message.strip()
                msg_parts = message.split(' ')
                if message.startswith(' '):
                    action = msg_parts[1]
                    msg_parts.insert(0, '')
                elif message.startswith('@'):
                    action = msg_parts[2]
                else:
                    action = ''
            except Exception, e:
                print e
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
                if c_msg["message"].find('­') != -1:
                    continue

                if self.__DB:
                    print datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ') + '#' + self.channel + ' ' + c_msg["sender"] + ": " + c_msg["message"].decode('utf-8')

                #Sub Message
                if c_msg["sender"] == 'twitchnotify':
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
                    if c_msg["message"].lower().find(self.t_trig) != -1:
                        if 'toobou' in self.command_times and self.config_data["toobou_output"] != "":
                            if self.time_check('toobou'):
                                self.twitch_send_message(self.config_data["toobou_output"])
                                self.command_times['toobou']['last'] = int(time.time())
                except:
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

                    elif c_msg["message"] == 'splits':
                        if self.game != '':
                            if self.command_check(c_msg, '!splits'):
                                self.splits_check()

                    elif c_msg["message"].startswith('addquote'):
                        if self.command_check(c_msg, '!addquote'):
                            self.add_text('quote', c_msg)

                    elif c_msg["message"] == 'quote':
                        if self.command_check(c_msg, '!quote'):
                            self.text_retrieve('quote')

                    elif c_msg["message"].startswith('addpun'):
                        if self.command_check(c_msg, '!addpun'):
                            self.add_text('pun', c_msg)

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

                    elif c_msg["message"].startswith('createvote ') and c_msg["tags"]["user_type"] in self.elevated_user:
                        self.create_vote(c_msg)

                    elif c_msg["message"] == 'endvote' and c_msg["tags"]["user_type"] in self.elevated_user:
                        self.end_vote()

                    elif c_msg["message"].startswith('vote '):
                        if self.command_check(c_msg, '!vote'):
                            self.vote(c_msg)

                    elif c_msg["message"] == 'checkvotes':
                        if self.command_check(c_msg, '!vote'):
                            self.check_votes(c_msg)

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
            if self.config_data["social_active"]:
                if self.messages_received >= (self.command_times['social']['messages'] + self.command_times['social']['messages_last']):
                    if int(time.time()) >= ((self.command_times['social']['time'] * 60) + self.command_times['social']['time_last']):
                        self.twitch_send_message(self.social_text)
                        self.command_times['social']['time_last'] = int(time.time())
                        self.command_times['social']['messages_last'] = self.messages_received

        print "thread stoped"
    #@@ ADMIN FUNCTIONS @@#

    def socket_error_restart(self):
        self.irc.close()
        self.irc = socket.socket()
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
        self.irc.sendall("QUIT\r\n")
        self.irc.close()
        
#@@BOT END@@#

def osu_send_message(osu_irc_pass, osu_nick, msg, sender):
    #Send the message through IRC to the person playing osu
    full_msg = "{}: {}".format(sender, msg)
    irc = socket.socket()
    osu_host = 'irc.ppy.sh'
    osu_port = 6667
    irc.connect((osu_host, osu_port))
    irc.sendall('PASS {}\r\n'.format(osu_irc_pass))
    irc.sendall('NICK {}\r\n'.format(osu_irc_nick))
    irc.sendall('PRIVMSG {} :{}\r\n'.format(osu_nick, full_msg))
    irc.sendall('QUIT\r\n')
    irc.close()

def twitch_info_grab(bots):
    #Grab all the people using the bots data in one call using stream objects

    channels = bots.keys()
    new_info = {}
    for i in channels:
        new_info[i] = {"game" : '', "title" : '', "start" : None}
    url = 'https://api.twitch.tv/kraken/streams?channel=' + ','.join(channels)
    headers = {'Accept' : 'application/vnd.twitchtv.v3+json'}
    try:
        data = requests.get(url, headers = headers)
        if data.status_code == 200:
            data_decode = data.json()
            if not data_decode['streams']:
                for k, v in new_info.iteritems():
                    bots[k].twitch_info(v["game"], v["title"], v["start"])
                return
            for i in data_decode['streams']:
                new_info[i['channel']['name']] = {"game" : i['channel']['game'],
                                                "title" : i['channel']['status'],
                                                "start" : i["created_at"]}
            for k, v in new_info.iteritems():
                bots[k].twitch_info(v["game"], v["title"], v["start"])

        else:
            pass
    except Exception, e:
        print e

def restart_bot(bot_name, bot_config, bot_dict):
    del bot_dict[bot_name]
    bot_dict[bot_name] = SaltyBot(bot_config[bot_name], debuging)
    bot_dict[bot_name].start()
        
def automated_main_loop(bot_dict, config_dict):
    time_to_check_twitch = 0
    next_buffer_clear = 0

    #time_to_restart = int(time.time()) + 86400 #Restart every 24 hours
    while True:
        try:
            register = interface.get(False) #returns [type of call, bot id that called it] therefore TYPE, DATA

            if register: 
                if register[TYPE] == RESTART:
                    restart_bot(register[DATA].channel, config_dict, bot_dict)

                if register[TYPE] == STOP:
                    raise 

                if register[TYPE] == CHECK:
                    for bot_name,bot_inst in bot_dict.items():
                        print bot_name+': '+bot_inst.thread
                        
                register = None

        except:
            pass

        current_time = int(time.time())

        if next_buffer_clear < current_time:
            for bot_name, bot_inst in bot_dict.items():
                bot_inst.clear_limiter()
            next_buffer_clear = int(time.time()) + 30

        if time_to_check_twitch < current_time:
            for bot_name, bot_inst in bot_dict.items():
                if bot_inst.thread.isAlive():
                    if debuging == True:
                        #print '#' + bot_name  + ': Is still running'
                        pass
                    
                else:
                    if debuging == True:
                        print '#' + bot_name + ' Had to restart'
                    restart_bot(bot_inst.channel, config_dict, bot_dict)

            twitch_info_grab(bot_dict)
            
            time_to_check_twitch = int(time.time()) + 60

def main():

    bot_dict = {} #Bot instances go in here
    channels_dict = {} #All channels go in here from the JSON file
    
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(db_url)
    db = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port

    try:
        conn = psycopg2.connect(database=db, user=user, host=host, password=password, port=port)
    except Exception, e:
        print e

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT * from users u
                JOIN Settings s on u.id=s.user_id
                WHERE s.active=true""")
    users = cur.fetchall()

    cur.execute("""SELECT * FROM commands c
                WHERE c.user_id in (SELECT s.user_id FROM Settings s WHERE s.active=true)""")
    commands = cur.fetchall()

    cur.execute("""SELECT * from custom_commands c
                WHERE c.user_id in (SELECT s.user_id FROM Settings s WHERE s.active=true)""")
    custom_commands = cur.fetchall()
    cur.close()
    conn.close()
    users_dict = {}
    for i in users:
        users_dict[i["id"]] = i
        users_dict[i["id"]]["commands"] = []
        users_dict[i["id"]]["custom_commands"] = []

    for i in commands:
        users_dict[i["user_id"]]["commands"].append(i)

    for i in custom_commands:
        users_dict[i["user_id"]]["custom_commands"].append(i)
    for k, v in users_dict.iteritems():
        channels_dict[v["twitch_name"]] = v

    for channel_name, channel_data in channels_dict.items(): #Start bots
        # Create bot and put it by name into a dictionary 

        bot_dict[channel_name] = SaltyBot(channel_data, debuging)

        info = bot_dict[channel_name].api_caller("https://api.twitch.tv/kraken/", headers={"Authorization" : "OAuth " + bot_dict[channel_name].twitch_oauth[6:]})
        if not (info["token"]["valid"] and "chat_login" in info["token"]["authorization"]["scopes"] and info["token"]["user_name"] == bot_dict[channel_name].twitch_nick.lower()):
            del bot_dict[channel_name]
            continue
        
        # Look up bot and start the thread
        bot_dict[channel_name].start()
        
        # Wait for twitch limit
        time.sleep(1)

    otherT = threading.Thread(target = automated_main_loop, args = (bot_dict, channels_dict))
    otherT.setDaemon(True)
    otherT.start()

    while True:
        command = raw_input("> ")
        if command.startswith("/brcs"):
            for bot,inst in bot_dict.items():
                inst.twitch_send_message("[Broadcast message]: "+(' '.join(command.split(' ')[1:])))
                
        if command.startswith("/stop"):
            for bot, inst in bot_dict.items():
                inst.stop()
                
            sys.exit()()
            
            
if __name__ == '__main__':
    try:
        main()
        
    except KeyboardInterrupt:
        print "Shut-down initiated..."


#make web page that doesn't suck
