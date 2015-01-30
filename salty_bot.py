#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import sys
import time
from datetime import datetime
import random
import threading
import socket
import requests
import json
import urlparse
import Queue as Q
import re
#import salty_util
debuging = True
Config_file_name = 'dConfig.json' if debuging else 'config.json'
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
#super users are used for bot breaking commands and beta commands
SUPER_USER = general_config['general_info']['super_users']

class SaltyBot:

    running = True
    messages_received = 0

    def __init__(self, config_data, debug = False):
        self.__DB = debug
        self.config_data = config_data
        self.irc = socket.socket()
        self.irc.settimeout(600)
        self.twitch_host = "irc.twitch.tv"
        self.port = 6667
        self.twitch_nick = config_data['general']['twitch_nick']
        self.twitch_oauth = config_data['general']['twitch_oauth']
        self.channel = config_data['general']['channel']
        self.game = ''
        self.title = ''
        self.time_start = ''
        self.commands = []
        self.admin_commands = []
        self.blacklist = []
        self.t_trig = None
        with open('{}_blacklist.txt'.format(self.channel), 'a+') as data_file:
            blacklist = data_file.readlines()
        for i in blacklist:
            self.blacklist.append(i.split('\n')[0])
        self.command_times = {}
        with open('{}_admins.txt'.format(self.channel), 'a+') as data_file:
            self.admin_file = data_file.read()

    def start(self):
        self.thread = threading.Thread(target=self.twitch_run)
        self.thread.setDaemon(True)
        self.thread.start()

        return self.thread

    def twitch_info(self, game, title, live):
        #Game can be nil (None) if left blank on Twitch, therefore check is neccessary
        self.game = game.lower() if game != None else game
        self.game_normal = game
        self.title = title.lower() if game != None else title
        self.time_start = live

    def twitch_connect(self):
        #Connect to Twitch IRC
        if self.__DB:
            print "Joining {} as {}.\n".format(self.channel,self.twitch_nick)
        try:
            #If it fails to conenct try again in 60 seconds
            self.irc.connect((self.twitch_host, self.port))
        except:
            print '{} failed to connect.'.format(self.channel)
            print sys.exc_info()[0]
            time.sleep(60)
            self.twitch_connect()

        self.irc.sendall('PASS {}\r\n'.format(self.twitch_oauth))
        self.irc.sendall('NICK {}\r\n'.format(self.twitch_nick))
        initial_msg = self.irc.recv(4096)
        if initial_msg == ':tmi.twitch.tv NOTICE * :Login unsuccessful\r\n':
            self.irc.sendall('QUIT\r\n')
            self.running = False
            del self
            print "{} has failed to use legitimate authentication.".format(self.channel)
        else:
            self.irc.sendall('JOIN #{}\r\n'.format(self.channel))


    def twitch_commands(self):
        #Set up all the limits, if its admin, if its on, quote and pun stuff, and anything else that needs setting up for a command
        for keys in self.config_data['commands']:
            if self.config_data['commands'][keys]['on']:
                self.commands.append(keys)
            if self.config_data['commands'][keys]['admin']:
                self.admin_commands.append(keys)
            self.command_times[keys] = {'last' : 0,
                                        'limit' : self.config_data['commands'][keys]['limit']}

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

        if self.config_data['general']['social']['text'] != '':
            self.command_times['social'] = {'time_last' : int(time.time()),
                                            'messages' : self.config_data['general']['social']['messages'],
                                            'messages_last' : self.messages_received,
                                            'time' : self.config_data['general']['social']['time']}
            self.social_text = self.config_data['general']['social']['text']

        if self.config_data['general']['toobou']['on'] == True:
            self.t_trig = self.config_data['general']['toobou']['trigger']
            self.command_times['toobou'] = {'trigger' : self.config_data['general']['toobou']['trigger'],
                                            'last' : 0,
                                            'limit' : self.config_data['general']['toobou']['limit']}

        if self.config_data['general']['custom']['on'] == True:
            self.command_times['custom'] = {'triggers' : self.config_data['general']['custom']['triggers'],
                                            'outputs' : self.config_data['general']['custom']['output'],
                                            'admins' : self.config_data['general']['custom']['admins'],
                                            'limits' : self.config_data['general']['custom']['limits'],
                                            'lasts' : []}
            for i in self.command_times['custom']['triggers']:
                self.command_times['custom']['lasts'].append(0)
                self.commands.append(('!' + i))
            for i in self.command_times['custom']['admins']:
                if self.command_times['custom']['admins'][i] == True:
                    self.admin_commands.append(self.command_times['custom']['admins'][i])

    def live_commands(self):
        #Remove any commands that would not currently work when !commands is used
        active_commands = list(self.commands)

        if not self.time_start:
            try:
                active_commands.remove('!uptime')
            except:
                pass

        if self.game == '':
            try:
                active_commands.remove('!wr')
            except:
                pass
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
        
        if 'race' not in self.title and 'races' not in self.title and 'racing' not in self.title:
            try:
                active_commands.remove('!race')
            except:
                pass

        command_string = ', '.join(active_commands)
        if command_string == '!commands':
            self.twitch_send_message('There are no current active commands.', '!commands')
        else:
            self.twitch_send_message(command_string, '!commands')

    def twitch_send_message(self, response, command = ''):

        #Sending any message to chat goes through this function
        try:
            response = response.encode('utf-8')
        except:
            pass
        if response.startswith('/me'):
            #Grant exception for /me because it can't do any harm
            pass
        elif response.startswith('.') or response.startswith('/'):
            #Prevent people from issuing server commands since bot is usually mod (aka /ban)
            response = "Please stop trying to abuse me BibleThump"
            command = ''
        to_send = 'PRIVMSG #{} :{}\r\n'.format(self.channel, response)
        self.irc.sendall(to_send)

        if self.__DB == True: 
            try:
                db_message = '#' + self.channel + ' ' + self.twitch_nick + ": " + response.decode('utf-8')
                db_message = db_message.encode('utf-8')
                print datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ') + db_message
            except:
                print("Message contained unicode, could not display in terminal\n\n")

        if command != '':
            #Update when the command was last used for rate limiting
            self.command_times[command]['last'] = int(time.time())

    def command_check(self, command):
        #Finds if the user can use said command, and then if the command is off cooldown
        #Will only return True if it's off cooldown and the user has the priviledges for the command
        if command in self.commands:
            if command in self.admin_commands:
                if self.sender in self.admin_file or self.sender == self.channel:
                    return True
                else:
                    return False
            else:
                if self.time_check(command):
                    return True
                else:
                    return False

    def time_check(self, command):
        #Return the current time minus the time the command was last used (used to make sure its off cooldown)
        return int(time.time()) - self.command_times[command]['last'] >= self.command_times[command]['limit']

    def is_live(self, user):
        #Checks to see if the racer on SRL is streaming to twitch and is live to build the multitwitch link
        url = 'https://api.twitch.tv/kraken/streams/' + user
        headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}
        data_decode = self.api_caller(url, headers)
        if data_decode == False:
            #If it fails to retrieve a json object, I give benefit of the doubt and say he is streaming
            return True
        data_stream = data_decode['stream']
        if data_stream == None:
            return False
        else:
            return True

    def api_caller(self, url, headers = None):
        #Call JSON api's for other functions
        if self.__DB: print url

        try:
            data = requests.get(url, headers = headers)
            if data.status_code == 200:
                data_decode = data.json()
                return data_decode
            else:
                return False
        except:
            print sys.exc_info()[0]
            return False

    def osu_api_user(self):
        #Perform a simple check of basic user stats on osu
        osu_nick = self.config_data['general']['osu']['osu_nick']
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
        osu_nick = self.config_data['general']['osu']['osu_nick']
        url = 'https://leagueofnewbs.com/api/user/{}/songs'.format(self.channel)
        data_decode = self.api_caller(url)
        if data_decode:
            print data_decode

    def osu_link(self):
        #Sends beatmaps linked in chat to you on osu, and then displays the map title and author in chat
        osu_nick = self.config_data['general']['osu']['osu_nick']

        if self.message_body.find('osu.ppy.sh/s/') != -1:
            osu_number = 's=' + self.message_body.split('osu.ppy.sh/s/')[-1].split(' ')[0]
        elif self.message_body.find('osu.ppy.sh/b/') != -1:
            osu_number = 'b=' + self.message_body.split('osu.ppy.sh/b/')[-1].split(' ')[0]

        osu_send_message(osu_irc_pass, osu_nick, self.message_body)

        url = 'https://osu.ppy.sh/api/get_beatmaps?k={}&{}'.format(osu_api_key, osu_number)
        data_decode = self.api_caller(url)
        if data_decode == False:
            return
        data_decode = data_decode[0]

        response = '{} - {}, mapped by {}'.format(data_decode['artist'], data_decode['title'], data_decode['creator'])
        self.twitch_send_message(response)

    def active_category(self, cats_array):
        categories_in_title = []
        category_position = {}
        
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

    def wr_retrieve(self):
        #Find the categories that are on file in the title, and then if more than one exist pick the one located earliest in the title
        categories_in_title = []
        category_position = {}
        url = 'http://www.speedrun.com/api_records.php?game=' + self.game
        game_records = self.api_caller(url)
        if game_records == False:
            self.twitch_send_message("I'm sorry, I couldn't retrieve the game's records from speedrun.com BibleThump", '!wr')
            return
        else:
            sr_game = dict(game_records).keys()[0]
            if sr_game.lower() == self.game.lower():
                sr_game_cats = game_records[sr_game].keys()
                for i in sr_game_cats:
                    if i.lower() in self.title:
                        categories_in_title.append(i)
                categories_in_title = list(set(categories_in_title))
            else:
                self.twitch_send_message("It appears the game is not on speedrun.com BibleThump", "!wr")
                return

            if len(categories_in_title) == 0:
                self.twitch_send_message("I'm sorry, but this category does not exist on speedrun.com", '!wr')
                return
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
            cat_record = game_records[sr_game][active_cat]
            wr_time = self.format_sr_time(cat_record['time'])
            msg = "The current world record for {} {} is {} by {}.".format(sr_game, active_cat, wr_time, cat_record['player'])
            if cat_record['video']:
                msg += "  The video can be found here: " + cat_record['video']
            self.twitch_send_message(msg, '!wr')

    def leaderboard_retrieve(self):
        #Retrieve leaderboard for game as set on Twitch
        game_no_spec = re.sub(' ', '_', self.game_normal)
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

    def add_text(self, text_type, text_add):
        #Add a pun or quote to the review file
        text = text_add[(len(text_type) + 4):]
        text = text.strip()
        print text

        if text == 'add{}'.format(text_type) or text == 'add{} '.format(text_type):
            self.twitch_send_message('Please input a {}.'.format(text_type))
        elif False:
            #DB connection insert into database!
            pass
        
            #Keeping this else to store quotes incase something really goes wrong.
        else:
            if self.sender == self.channel:
                #If person adding is channel owner, it goes straight to the live file
                with open('{}_{}.txt'.format(self.channel, text_type), 'a+') as data_file:
                    data_file.write('{}\n'.format(text))
                response = 'Your {} has been added.'.format(text_type)
                self.twitch_send_message(response)
            else:
                with open('{}_{}_review.txt'.format(self.channel, text_type), 'a+') as data_file:
                    data_file.write('{}\n'.format(text))
                response = 'Your {} has been added for review.'.format(text_type)
                self.twitch_send_message(response)

    def text_retrieve(self, text_type):
        #Pull a random pun/quote from the live file
        #Will not pull the same one twice in a row
        with open('{}_{}.txt'.format(self.channel, text_type), 'a+') as data_file:
            lines_read = data_file.readlines()
        lines = sum(1 for line in lines_read)
        if lines == 0:
            response = 'No {}s have been added.'.format(text_type)
            self.this_retrieve = response
        elif lines == 1:
            response = lines_read[0].encode('utf-8')
            self.this_retrieve = response
        else:
            response = lines_read[random.randint(0, lines -1 )]
            while response == self.last_text[text_type]:
                response = lines_read[random.randint(0, lines - 1)]

        self.twitch_send_message(response, '!' + text_type)
        self.last_text[text_type] = response

    def srl_race_retrieve(self):
        #Goes through all races, finds the race the user is in, gathers all other users in the race, prints the game, the 
        #category people are racing, the time racebot has, and either a multitwitch link or a SRL race room link
        self.srl_nick = self.config_data['general']['srl_nick']
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
                            response += ', Finished {} with a time of {}'.format(user_place, time_formatted)
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

    def youtube_video_check(self, vid_type, message):
        #Links the title and uploader of the youtube video in chat
        if vid_type == 'short':
            video_id = message.split('youtu.be/')[-1]
        else:
            url_values = urlparse.parse_qs(urlparse.urlparse(message).query)
            try:
                video_id = url_values['v'][0]
            except:
                return

        if ' ' in video_id:
            video_id = video_id.split(' ')[0]

        url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={}&key={}'.format(video_id, youtube_api_key)
        data_decode = self.api_caller(url)

        if data_decode == False:
            return

        if len(data_decode['items']) != 0:
            data_items = data_decode['items']
            youtube_title = data_items[0]['snippet']['title'].encode("utf-8")
            youtube_uploader = data_items[0]['snippet']['channelTitle'].encode("utf-8")
            response = '{} uploaded by {}'.format(youtube_title, youtube_uploader)
            self.twitch_send_message(response)
        else:
            return

    def create_vote(self, message):
        #Used to create polls in chat
        #Creating polls requires a pretty specific syntax, but makes it easy to have different types
        if self.votes:
            self.twitch_send_message('There is already an open poll, please close it first.')
            return
        
        poll_type = message.split(' ')[1]

        try:
            poll = re.findall('"(.+)"', message)[0]
        except:
            self.twitch_send_message('Please give the poll a name.')
            return

        self.votes = {  'name' : poll,
                        'type' : poll_type,
                        'options' : {},
                        'voters' : {}}

        if poll_type == 'strict':
            options = re.findall('\((.+?)\)', message)

            if not options:
                self.twitch_send_message('You did not supply any options, poll will be closed.')
                self.votes.clear()
                return

            for i in options:
                i = i.lower()
                self.votes['options'][i] = 0
            response = 'You may now vote for this poll using only the supplied options.'

        elif poll_type == 'loose':
            response = 'You may now vote for this poll with whatever choice you like.'

        self.twitch_send_message(response)

    def end_vote(self):
        #Ending a current poll will display the winning vote of the poll and close it
        if self.votes:
            try:
                winning_key = max(self.votes['options'], key = self.votes['options'].get)
                winning_value = self.votes['options'][winning_key]
                self.votes.clear()
                response = '{} has won with {} votes.'.format(winning_key, str(winning_value))
            except ValueError:
                self.votes.clear()
                response = ''
            self.twitch_send_message(response)

    def vote(self, message, sender):
        #Allows viewers to vote in a poll created by mods/broadcaster
        try:
            sender_bet = message.split('vote ')[-1]
            sender_bet = sender_bet.lower()
        except:
            return
        if not self.votes:
            return

        if self.votes['type'] == 'strict':
            if sender_bet not in self.votes['options']:
                self.twitch_send_message('You must vote for one of the options specified: ' + ', '.join(self.votes['options'].keys()), '!vote')
                return

        if sender in self.votes['voters']:
            if sender_bet == self.votes['voters'][sender]:
                response = 'You have already voted for that {}.'.format(sender)
            else:
                previous = self.votes['voters'][sender]
                self.votes['options'][previous] -= 1

                if self.votes['options'][previous] == 0 and self.votes['type'] == 'loose':
                    del self.votes['options'][previous]

                try:
                    self.votes['options'][sender_bet] += 1
                except KeyError:
                    self.votes['options'][sender_bet] = 1

                self.votes['voters'][sender] = sender_bet
                response = '{} has changed their vote to {}'.format(sender, sender_bet)
        else:
            try:
                self.votes['options'][sender_bet] += 1
            except KeyError:
                self.votes['options'][sender_bet] = 1

            self.votes['voters'][sender] = sender_bet
            response = '{} now has {} votes for it.'.format(sender_bet, str(self.votes['options'][sender_bet]))

        self.twitch_send_message(response, '!vote')

    def check_votes(self, message):
        #Allows you to see what is currently winning in the current poll w/o closing it
        if not self.votes:
            return

        if not self.votes['options']:
            response = 'No one has bet yet.'

        else:
            winning_key = max(self.votes['options'], key = self.votes['options'].get)
            winning_value = self.votes['options'][winning_key]
            response = '{} is winning with {} votes for it.'.format(winning_key, winning_value)

        self.twitch_send_message(response, '!vote')

    def text_review(self, message, last_r = 'none'):
        #Review puns/quotes through chat (spammy as shit), better implementation will be available in the website
        try:
            text_type = message.split(' ')[1]
            if text_type != 'quote' and text_type != 'pun':
                return
        except:
            self.twitch_send_message('Please specify a type to review.')
            return
        try:
            decision = message.split(' ')[2]
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

    def lister(self, message, s_list):
        #Add user to blacklist or remove them from it
        #Blacklist will cause bot to completely ignore the blacklisted user
        user = message.split(' ')[-1]
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

    def custom_command(self, message, sender):
        #Shitty custom command implementation, 
        space_count = message.count(' ')
        if space_count == 0:
            command = message
            param = ''
        else:
            command = message.split(' ')[0]
            param = message.split(' ')[-space_count]
        if command not in self.command_times['custom']['triggers']:
            return
        if command in self.admin_commands and sender not in self.admin_file:
            return
        location = self.command_times['custom']['triggers'].index(command)
        if int(time.time()) - self.command_times['custom']['lasts'][location] <= self.command_times['custom']['limits'][location]:
            return
        output = self.command_times['custom']['outputs'][location]
        output = re.sub('\$sender', sender, output)
        output = re.sub('\$param', param, output)
        self.twitch_send_message(output)
        self.command_times['custom']['lasts'][location] = int(time.time())

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
        current_object = datetime(current_time[0], current_time[1], current_time[2], current_time[3], current_time[4], current_time[5])

        time_live_split = re.split("(\d{4}?)-(\d{2}?)-(\d{2}?)T(\d{2}?):(\d{2}?):(\d{2}?)Z", self.time_start)[1:-1]
        for i, s in enumerate(time_live_split):
            time_live_split[i] = int(s)
        live_object = datetime(time_live_split[0], time_live_split[1], time_live_split[2], time_live_split[3], time_live_split[4], time_live_split[5])
        
        return current_object, live_object

    def uptime(self):
        if not self.time_start:
            current_object, live_object = self.get_time_objects()
            total_live_object = current_object - live_object
            self.twitch_send_message("The current stream has been live for " + str(total_live_object), '!uptime')
        else:
            self.twitch_send_message("The stream is not currently live.", '!uptime')

    def highlight(self, message):
        if not self.time_start:
            current_object, live_object = self.get_time_objects()
            time_to_highlight = current_object - live_object
            self.to_highlight.append({'time' : time_to_highlight, 'desc' : message.split('highlight')[-1]})
            self.twitch_send_message("Current time added to the highlight queue. Use !show_highlight to view them.")
        else:
            self.twitch_send_message("Please use the command when the stream is live.")

    def show_highlight(self):
        msg = "Things you need to highlight: "
        for i in self.to_highlight:
            msg += i['time'] + " @ " + i['desc'] + ", "
        self.twitch_send_message(msg[:-2])
        self.to_highlight = []

    def sub_msg(self, msg):
        pass

    def twitch_run(self):
        #Main loop for running the bot
        self.twitch_connect()   #Connect to IRC
        self.twitch_commands()  #Get all the commands in order

        while self.running:

            try:
                self.message = self.irc.recv(4096)
            except socket.timeout:
                print self.channel + ' timed out.'
                self.socket_error_restart()

            if self.message == "":
                print self.channel + ' returned empty string.'
                self.socket_error_restart()

            self.message = self.message.split('\r\n')[0]
            self.message = self.message.strip()

            if self.message.startswith('PING'):
                self.irc.sendall('PONG tmi.twitch.tv\r\n')

            try:
                self.action = self.message.split(' ')[1]
            except:
                if self.message:
                    print datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ') + self.message
                self.action = ''

            if self.action == 'PRIVMSG':
                #Messages to channel are PRIVMSG's, just aimed at a channel instead of a user
                self.messages_received += 1
                self.sender = self.message.split(':')[1].split('!')[0]
                self.message_body = ':'.join(self.message.split(':')[2:])
                if self.sender in self.blacklist:
                    continue
                if self.message_body.find('­') != -1:
                    continue

                if self.__DB:
                    print datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ') + '#' + self.channel + ' ' + self.sender + ": " + self.message_body.decode('utf-8')

                #Sub Message
                if self.sender == 'twitchnotify':
                    self.sub_msg(self.message)

                #Link osu maps
                if self.message_body.find('osu.ppy.sh/b/') != -1 or self.message_body.find('osu.ppy.sh/s/') != -1:
                    if self.game == 'osu!':
                        if self.config_data['general']['osu']['song_link']:
                            self.osu_link()

                #Link youtube info
                if self.message_body.find('youtube.com/watch?v=') != -1:
                    if self.config_data['general']['youtube_link']:
                        self.youtube_video_check('long', self.message_body)

                #Link youtube info
                if self.message_body.find('youtu.be/') != -1:
                    if self.config_data['general']['youtube_link']:
                        self.youtube_video_check('short', self.message_body)

                #Toobou trigger check
                try:
                    if self.message_body.lower().find(self.t_trig) != -1:
                        if 'toobou' in self.command_times:
                            if self.time_check('toobou'):
                                self.twitch_send_message(self.config_data['general']['toobou']['insult'])
                                self.command_times['toobou']['last'] = int(time.time())
                except:
                    pass
                    
                if self.message_body.startswith('!'):
                    #Dirty work around to allow text to have more !'s in them
                    find_ex = self.message_body.count('!')
                    self.message_body = '!'.join(self.message_body.split('!')[-find_ex:])

                    #All commands go here

                    if self.config_data['general']['custom']['on'] == True:
                        self.custom_command(self.message_body, self.sender)

                    if self.message_body.startswith('blacklist ') and self.sender == self.channel:
                        self.lister(self.message_body, 'black')

                    elif self.message_body.startswith('whitelist ') and self.sender == self.channel:
                        self.lister(self.message_body, 'white')

                    elif self.message_body.startswith('wr'):
                        if self.game != '':
                            if self.command_check('!wr'):
                                self.wr_retrieve()

                    elif self.message_body.startswith('leaderboard'):
                        if self.game != '':
                            if self.command_check('!leaderboard'):
                                    self.leaderboard_retrieve()

                    elif self.message_body == 'splits':
                        if self.game != '':
                            if self.command_check('!splits'):
                                self.splits_check()

                    elif self.message_body.startswith('addquote'):
                        if self.command_check('!addquote'):
                            self.add_text('quote', self.message_body)

                    elif self.message_body == 'quote':
                        if self.command_check('!quote'):
                            self.text_retrieve('quote')

                    elif self.message_body.startswith('addpun'):
                        if self.command_check('!addpun'):
                            self.add_text('pun', self.message_body)

                    elif self.message_body == 'pun':
                        if self.command_check('!pun'):
                            self.text_retrieve('pun')

                    elif self.message_body == 'rank':
                        if self.game == 'osu!':
                            if self.command_check('!rank'):
                                self.osu_api_user()

                    elif self.message_body == 'song':
                        if self.game == 'osu!':
                            if self.command_check('!song'):
                                self.osu_song_display()

                    elif self.message_body == 'race':
                        if 'race' in self.title or 'races' in self.title or 'racing' in self.title:
                            if self.command_check('!race'):
                                self.srl_race_retrieve()

                    elif self.message_body.startswith('createvote ') and self.sender in self.admin_file:
                        self.create_vote(self.message_body)

                    elif self.message_body == 'endvote' and self.sender in self.admin_file:
                        self.end_vote()

                    elif self.message_body.startswith('vote '):
                        if self.command_check('!vote'):
                            self.vote(self.message_body, self.sender)

                    elif self.message_body == 'votes':
                        if self.command_check('!vote'):
                            self.check_votes(self.message_body)

                    elif self.message_body.startswith('review') and self.sender == self.channel:
                        self.text_review(self.message_body)

                    elif self.message_body == 'runes':
                        if self.game == 'league of legends':
                            if self.command_check('!runes'):
                                self.lol_runes()

                    elif self.message_body == "masteries":
                        if self.game == 'league of legends':
                            if self.command_check('!masteries'):
                                self.lol_masteries()

                    elif self.message_body == "uptime":
                        if self.command_check('!uptime'):
                            self.uptime()

                    elif self.message_body.startswith('highlight'):
                        if self.sender == self.channel or self.sender in SUPER_USER:
                            self.highlight(self.message_body)

                    elif self.message_body == "show_highlight":
                        if self.sender == self.channel or self.sender in SUPER_USER:
                            self.show_highlight()
                        
                    elif self.message_body == 'commands':
                        if self.time_check('!commands'):
                            self.live_commands()

                    elif self.message_body == 'bot_info':
                        self.twitch_send_message('Powered by SaltyBot, for a full list of commands check out https://github.com/batedurgonnadie/salty_bot#readme')

                    elif self.message_body == 'restart' and self.sender in SUPER_USER:
                        if self.__DB:
                            print('{} is restarting, called by {}'.format(self.channel + ' ' + self.twitch_nick, self.sender))
                        self.admin(RESTART)
                        self.twitch_send_message('Restarting the bot.')
                        break

                    elif self.message_body == 'check' and self.sender in SUPER_USER:
                        self.admin(CHECK)
                        
                    elif self.message_body == 'crash' and self.sender in SUPER_USER:
                        self.running = False

                    #Commands end heree

            elif self.action == 'MODE':
                #Adds users to the mod list
                #Currently never removes them, I assume if they got modded once they are trust worthy to use all commands
                #TMI also loves to drop mod status, which would break mod commands if it removed them as it de-op'd
                # THIS IS GOING TO BE RE-WRITTEN FOR IRCv3 ONCE IT IS RELEASED
                if '+o ' in self.message:
                    admin = self.message.split('+o ')[-1]
                    if admin not in self.admin_file:
                        with open('{}_admins.txt'.format(self.channel), 'a+') as data_file:
                            data_file.write('{}\n'.format(admin))
                        with open('{}_admins.txt'.format(self.channel), 'a+') as data_file:
                            self.admin_file = data_file.read()

            #Check the social down here, so that even if ping happens social can go off if the minimum time/messages are met but no one is talking
            if self.config_data['general']['social']['text'] != '':
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

def osu_send_message(osu_irc_pass, osu_nick, request_url):
    #Send the message through IRC to the person playing osu
    irc = socket.socket()
    osu_host = 'irc.ppy.sh'
    osu_port = 6667
    irc.connect((osu_host, osu_port))
    irc.sendall('PASS {}\r\n'.format(osu_irc_pass))
    irc.sendall('NICK {}\r\n'.format(osu_irc_nick))
    irc.sendall('PRIVMSG {} :{}\r\n'.format(osu_nick, request_url))
    irc.close()

def twitch_info_grab(bots):
    #Grab all the people using the bots data in one call using stream objects
    with open(Config_file_name, 'r') as data_file:
        channel_configs = json.load(data_file, encoding = 'utf-8')

    channels = channel_configs.keys()
    new_info = {}
    for i in channels:
        new_info[i] = {"game" : None, "title" : None, "start" : None}
    url = 'https://api.twitch.tv/kraken/streams?channel=' + ','.join(channels)
    headers = {'Accept' : 'application/vnd.twitchtv.v3+json'}
    try:
        data = requests.get(url, headers = headers)
        if data.status_code == 200:
            data_decode = data.json()
            if not data_decode['streams']:
                return
            for i in data_decode['streams']:
                new_info[i['channel']['name']] = {"game" : i['channel']['game'],
                                                "title" : i['channel']['status'],
                                                "start" : i["created_at"]}
            for k, v in new_info.iteritems():
                bots[k].twitch_info(v["game"], v["title"], v["start"])

        else:
            pass
    except Exception:
        print "Getting twitch data threw an exception"
        print sys.exc_info()[0]

def restart_bot(bot_name, bot_dict):
    with open(Config_file_name, 'r') as data_file:
        bot_config = json.load(data_file, encoding = 'utf-8')[bot_name]
        
    del bot_dict[bot_name]
    bot_dict[bot_name] = SaltyBot(bot_config, debuging)
    bot_dict[bot_name].start()
        
def automated_main_loop(bot_dict):
    time_to_check_twitch = 0
    #time_to_restart = int(time.time()) + 86400 #Restart every 24 hours
    while True:
        try:
            register = interface.get(False) #returns [type of call, bot id that called it] therefore TYPE, DATA

            if register: 
                if register[TYPE] == RESTART:
                    restart_bot(register[DATA].channel, bot_dict)

                if register[TYPE] == STOP:
                    raise 

                if register[TYPE] == CHECK:
                    for bot_name,bot_inst in bot_dict.items():
                        print bot_name+': '+bot_inst.thread
                        
                register = None

        except:
            pass

        if time_to_check_twitch < int(time.time()):
            for bot_name, bot_inst in bot_dict.items():
                if bot_inst.thread.isAlive():
                    if debuging == True:
                        #print '#' + bot_name  + ': Is still running'
                        pass
                    
                else:
                    if debuging == True:
                        print '#' + bot_name + ' Had to restart'
                    restart_bot(bot_inst.channel, bot_dict)

            twitch_info_grab(bot_dict)
            
            time_to_check_twitch = int(time.time()) + 60

def main():

    bot_dict = {} #Bot instances go in here
    channels_dict = {} #All channels go in here from the JSON file
    
    with open(Config_file_name, 'r') as data_file: #Get file data
        channels_dict = json.load(data_file, encoding = 'utf-8')

    for channel_name,channel_data in channels_dict.items(): #Start bots
        # Create bot and put it by name into a dictionary 
        bot_dict[channel_name] = SaltyBot(channel_data, debuging)
        
        # Look up bot and start the thread
        bot_dict[channel_name].start()
        
        # Wait for twitch limit
        time.sleep(2)

    otherT = threading.Thread(target = automated_main_loop, args = [bot_dict])
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
