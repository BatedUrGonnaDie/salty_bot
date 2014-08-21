#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import threading
import socket
import requests
import json
import urlparse
import Queue as Q
import re

debuging = False
Config_file_name = 'dConfig.json' if debuging else 'config.json'

SUPER_USER = ['batedurgonnadie','bomb_mask','glacials']
RESTART = "<restart>"
STOP = "<stop program>"
CHECK = "<check threads>"

TYPE = 0
DATA = 1

interface = Q.Queue()

with open('general_config.json', 'r') as data_file:
    general_config = json.load(data_file, encoding = 'utf-8')

lol_api_key = general_config['general_info']['lol_api_key']
youtube_api_key = general_config['general_info']['youtube_api_key']
osu_api_key = general_config['general_info']['osu']['osu_api_key']
osu_irc_nick = general_config['general_info']['osu']['osu_irc_nick']
osu_irc_pass = general_config['general_info']['osu']['osu_irc_pass']

games = general_config['games']

class SaltyBot:

    running = True
    messages_received = 0

    def __init__(self, config_data, debug = False):
        self.__DB = debug
        self.config_data = config_data
        self.irc = socket.socket()
        self.irc.settimeout(600)
        self.twitch_host = ['irc.twitch.tv', '199.9.252.120', '199.9.250.229', '199.9.250.239', '199.9.252.28']
        self.port = 6667
        self.twitch_nick = config_data['general']['twitch_nick']
        self.twitch_oauth = config_data['general']['twitch_oauth']
        self.channel = config_data['general']['channel']
        self.game = ''
        self.title = ''
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

    def twitch_info(self, game, title):
        self.game = game.lower() if game != None else game
        self.title = title.lower() if game != None else title

    def twitch_connect(self):
        connected = False
        if self.__DB:
            print "Joining {} as {}.\n".format(self.channel,self.twitch_nick)
        while connected == False:
            for i in self.twitch_host:
                try:
                    self.irc.connect((i, self.port))
                    connected = True
                    break
                except:
                    print '{} failed to connect to {}'.format(self.channel, i)
                    time.sleep(5)
                    continue
            if connected == False:
                time.sleep(30)

        self.irc.sendall('PASS {}\r\n'.format(self.twitch_oauth))
        self.irc.sendall('NICK {}\r\n'.format(self.twitch_nick))
        self.irc.sendall('JOIN #{}\r\n'.format(self.channel))

    def twitch_commands(self):
        for keys in self.config_data['commands']:
            if self.config_data['commands'][keys]['on']:
                self.commands.append(keys)
            if self.config_data['commands'][keys]['admin']:
                self.admin_commands.append(keys)
            self.command_times[keys] = {'last' : 0,
                                        'limit' : self.config_data['commands'][keys]['limit']}

        if '!vote' in self.commands:
            self.votes = {}

        if '!quote' in self.commands or '!pun' in self.commands:
            self.review = {}
            if '!quote' in self.commands:
                self.review['quote'] = []
            if '!pun' in self.commands:
                self.review['pun'] = []

        if self.config_data['general']['social']['text'] != '':
            self.command_times['social'] = {'time_last' : int(time.time()),
                                            'messages' : self.config_data['general']['social']['messages'],
                                            'messages_last' : self.messages_received,
                                            'time' : self.config_data['general']['social']['time']}
            self.social_text = self.config_data['general']['social']['text']

        if self.config_data['general']['toobou']['on'] == True:
            self.t_trig = self.config_data['general']['toobou']['trigger']
            self.command_times['toobou'] = {'trigger' : self.config_data['general']['toobou']['trigger'],
                                            'last' : int(time.time()),
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

        self.commands_string = ', '.join(self.commands)

    def twitch_send_message(self, response, command = ''):
        try:
            response = response.encode('utf-8')
        except:
            pass

        to_send = 'PRIVMSG #{} :{}\r\n'.format(self.channel, response)
        self.irc.sendall(to_send)

        if command != '':
            self.command_times[command]['last'] = int(time.time())

    def command_check(self, command):
        if command in self.commands:
            if command in self.admin_commands:
                if self.sender in self.admin_file:
                    return True
                else:
                    return False
            else:
                if self.time_check(command):
                    return True
                else:
                    return False


    def time_check(self, command):
        return int(time.time()) - self.command_times[command]['last'] >= self.command_times[command]['limit']

    def is_live(self, user):
        url = 'https://api.twitch.tv/kraken/streams/' + user
        headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}
        data_decode = self.api_caller(url, headers)
        if data_decode == False:
            return True
        data_stream = data_decode['stream']
        if data_stream == None:
            return False
        else:
            return True

    def api_caller(self, url, headers = None):
        if self.__DB:
            print url, "Headers: ", headers

        data = requests.get(url, headers = headers)
        if data.status_code == 200:
            data_decode = data.json()
            return data_decode
        else:
            return False

    def osu_api_user(self):
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

    def osu_link(self):
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

    def wr_retrieve(self):
        if self.game in games:
            for keys in games[self.game]['categories'].keys():
                if keys in self.title:
                    wr = games[self.game]['categories'][keys]
                    self.twitch_send_message(wr, '!wr')

    def leaderboard_retrieve(self):
        if self.game in games:
            leaderboard = games[self.game]['leaderboard']
            self.twitch_send_message(leaderboard, '!leaderboard')

    def add_text(self, text_type, text_add):
        text = text_add.split('{} '.format(text_type))[-1]

        if text == 'add{}'.format(text_type) or text == 'add{} '.format(text_type):
            self.twitch_send_message('Please input a {}.'.format(text_type))
        else:
            if self.sender == self.channel:
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
        with open('{}_{}.txt'.format(self.channel, text_type), 'a+') as data_file:
            lines_read = data_file.readlines()
        lines = sum(1 for line in lines_read)
        if lines == 0:
            response = 'No {}s have been added.'.format(text_type)
            self.this_retrieve = response
        elif lines == 1:
            response = lines_read[0]
            self.this_retrieve = response
        else:
            while True:
                try:
                    while self.this_retrieve == self.last_retrieve:
                        select_line = random.randrange(1, lines, 1)
                        response = lines_read[select_line]
                        self.this_retrieve = response
                except:
                    self.last_retrieve = ''
                    self.this_retrieve = ''
                    continue
                break
        self.twitch_send_message(response, '!' + text_type)
        self.last_retrieve = self.this_retrieve

    def srl_race_retrieve(self):
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
                        if values['statetext'] == 'Ready':
                            if values['twitch'] != '':
                                srl_race_entrants.append(values['twitch'])
                    user = i['entrants'][self.srl_nick]['twitch']
                    user_place = race_channel['entrants'][self.srl_nick]['place']
                    user_time = race_channel['entrants'][self.srl_nick]['time']
                    srl_race_game = race_channel['game']['name']
                    srl_race_category = race_channel['goal']
                    srl_race_id = race_channel['id']
                    srl_race_status = race_channel['statetext']
                    srl_race_time = race_channel['time']
                    srl_race_link = 'http://www.speedrunslive.com/race/?id={}'.format(srl_race_id)
                    srl_live_entrants = []
                    for j in srl_race_entrants:
                        if self.is_live(j):
                            srl_live_entrants.append(j)
                    multitwitch_link = 'www.multitwitch.tv/'
                    response = 'Game: {}, Category: {}, Status: {}'.format(srl_race_game, srl_race_category, srl_race_status)
                    if srl_race_time > 0:
                        if user_time > 0:
                            m, s = divmod(user_time, 60)
                            h, m = divmod(m, 60)
                            response += ', Finished {} with a time of {}:{}:{}'.format(user_place, h, m, s)
                        else:
                            real_time = (int(time.time()) - srl_race_time)
                            m, s = divmod(real_time, 60)
                            h, m = divmod(m, 60)
                            response += ', RaceBot Time: {}:{}:{}'.format(h, m, s)
                    if len(srl_live_entrants) <= 6:
                        for j in srl_live_entrants:
                            multitwitch_link += j + '/'
                        response += '.  {}'.format(multitwitch_link)
                    else:
                        response += '.  {}'.format(srl_race_id)
                    self.twitch_send_message(response, '!race')

    def youtube_video_check(self, message):
        url_values = urlparse.parse_qs(urlparse.urlparse(message).query)
        try:
            youtube_video_id = url_values['v'][0]
        except:
            return

        if ' ' in youtube_video_id:
            youtube_video_id = youtube_video_id.split(' ')[0]

        url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={}&key={}'.format(youtube_video_id, youtube_api_key)
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

    def youtube_short_check(self, message):
        video_id = message.split('youtu.be/')[-1]
        
        if ' ' in video_id:
            video_id.split(' ')[0]

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
        try:
            sender_bet = message.split('vote ')[-1]
            sender_bet = sender_bet.lower()
        except:
            print 'no bet'
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
            for text in self.review[text_type]:
                if text[1] == 0:
                    text[1] = 1
                    self.text_review('review {} next'.format(text_type), 'Approved')
                    return
            self.text_review('review {} next'.format(text_type))
        elif decision == 'reject':
            for text in self.review[text_type]:
                if text[1] == 0:
                    text[1] = 2
                    self.text_review('review {} next'.format(text_type), 'Rejected')
                    return
            self.text_review('review {} next'.format(text_type))
        elif decision == 'commit':
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
            self.twitch_send_message('Approved {}s moved to the live file.'.format(text_type))
        else:
            for text in self.review[text_type]:
                if text[1] == 0:
                    if last_r == 'none':
                        self.twitch_send_message(text[0])
                        return
                    else:
                        self.twitch_send_message(last_r + ", next quote: " + text[0])
                        return
            if self.review[text_type]:
                self.twitch_send_message('Please use "!review {} commit" to lock the changes in place.'.format(text_type))
            else:
                self.twitch_send_message('Nothing to review in {}.'.format(text_type))

    def lister(self, message, s_list):
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
        if output.count(' ') != 0:
            out_a = output.split(' ')
        else:
            out_a = [output]
        for i in out_a:
            if i == '$sender':
                t_location = out_a.index(i)
                out_a[t_location] = sender
            elif i == '$param':
                t_location = out_a.index(i)
                out_a[t_location] = param
        out_final = ' '.join(out_a)
        self.twitch_send_message(out_final)
        self.command_times['custom']['lasts'][location] = int(time.time())
    
    def lol_masteries(self):
        self.summoner_name = 'batedurgonnadie'
        name_url = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format(self.summoner_name, lol_api_key)
        name_data = self.api_caller(name_url)
        if name_data == False:
            return
        summoner_id = name_data[self.summoner_name]['id']
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
        self.twitch_send_message(response)

    def lol_runes(self):
        self.summoner_name = 'batedurgonnadie'
        
        name_url = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format(self.summoner_name, lol_api_key)
        name_data = self.api_caller(name_url)
        
        if name_data == False:
            return
            
        summoner_id = name_data[self.summoner_name]['id']
        rune_url = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/{}/runes?api_key={}'.format(summoner_id, lol_api_key)
        rune_data = self.api_caller(rune_url)
        
        if rune_data == False:
            return
            
        for i in rune_data[str(summoner_id)]['pages']:
            if i['current'] == True:
                active_page = i
                break

        rune_str_list = []
        counted_rune_data = {}

        with open("runes.json",'r') as fin:
            runes_list = json.load(fin, encoding="utf-8")

        for rune in active_page["slots"]:
            try:
                counted_rune_data[rune["runeId"]] += 1
            except KeyError:
                counted_rune_data[rune["runeId"]] = 1

        for k, v in counted_rune_data.items():
            k = str(k)
            current_rune = runes_list["data"][k]
            stat_number = current_rune["stats"].values()[0]

            description = current_rune["description"].split('(')

            stats = {}
            stats["stat"] = str( round( stat_number, 2) )
            stats["statlvl18"] = str( round( stat_number * 18, 2) )


            description[0] = re.sub("-?\d+\.\d+", stats["stat"], description[0])

            if len(description) == 2 :
                description[1] = re.sub("-?\d+\.\d+", stats["statlvl18"], description[1])

                rune_str_list += ['('.join(description)]
            else:
                rune_str_list += [description[0]]

        self.twitch_send_message("Page Name: {} : {}".format(active_page["name"], " | ".join(rune_str_list)))
   

    def twitch_run(self):
        self.twitch_connect()
        self.twitch_commands()

        while self.running:

            try:
                self.message = self.irc.recv(4096)
            except:
                self.irc.close()
                self.twitch_run()

            self.message = self.message.split('\r\n')[0]
            self.message = self.message.strip()

            if self.message.startswith('PING'):
                self.irc.sendall('PONG tmi.twitch.tv\r\n')

            try:
                self.action = self.message.split(' ')[1]
            except:
                self.action = ''

            if self.action == 'PRIVMSG':
                self.messages_received += 1
                self.sender = self.message.split(':')[1].split('!')[0]
                self.message_body = ':'.join(self.message.split(':')[2:])
                if self.sender in self.blacklist:
                    continue
                if self.message_body.find('­') != -1:
                    continue

                if self.message_body.find('osu.ppy.sh/b/') != -1 or self.message_body.find('http://osu.ppy.sh/s/') != -1:
                    if self.game == 'osu!':
                        if self.config_data['general']['osu']['song_link']:
                            self.osu_link()

                if self.message_body.find('youtube.com/watch?v=') != -1:
                    if self.config_data['general']['youtube_link']:
                        self.youtube_video_check(self.message_body)

                if self.message_body.find('youtu.be/') != -1:
                    if self.config_data['general']['youtube_link']:
                        self.youtube_short_check(self.message_body)

                try:
                    if self.message_body.lower().find(self.t_trig) != -1:
                        if 'toobou' in self.command_times:
                            if self.time_check('toobou'):
                                self.twitch_send_message(self.config_data['general']['toobou']['insult'])
                                self.command_times['toobou']['last'] = int(time.time())
                except:
                    pass

                if self.__DB:
                    print self.sender + ": " + self.message_body

                if self.message_body.startswith('!'):
                    find_ex = self.message_body.count('!')
                    self.message_body = self.message_body.split('!')[-find_ex]

                    if len(self.command_times['custom']['triggers']) != 0:
                        self.custom_command(self.message_body, self.sender)

                    if self.message_body.startswith('blacklist ') and self.sender == self.channel:
                        self.lister(self.message_body, 'black')

                    elif self.message_body.startswith('whitelist ') and self.sender == self.channel:
                        self.lister(self.message_body, 'white')

                    elif self.message_body.startswith('wr'):
                        if self.command_check('!wr'):
                            self.wr_retrieve()

                    elif self.message_body.startswith('leaderboard'):
                        if self.command_check('!leaderboard'):
                                self.leaderboard_retrieve()

                    elif self.message_body.startswith('addquote'):
                        if self.command_check('!quote'):
                            self.add_text('quote', self.message_body)

                    elif self.message_body == 'quote':
                        if self.command_check('!quote'):
                            self.text_retrieve('quote')

                    elif self.message_body.startswith('addpun'):
                        if self.command_check('!pun'):
                            self.add_text('pun', self.message_body)

                    elif self.message_body == 'pun':
                        if self.command_check('!pun'):
                            self.text_retrieve('pun')

                    elif self.message_body == 'rank':
                        if self.game == 'osu!':
                            if self.command_check('!rank'):
                                self.osu_api_user()

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

                    elif self.message_body == 'runes' and self.sender in SUPER_USER:
                        self.lol_runes()

                    elif self.message_body == "masteries" and self.sender in SUPER_USER:
                        self.lol_masteries()
                        
                    elif self.message_body == 'commands':
                        if self.time_check('!commands'):
                            self.twitch_send_message(self.commands_string, '!commands')

                    elif self.message_body == 'bot_info':
                        self.twitch_send_message('Powered by SaltyBot, for a full list of commands check out www.github.com/batedurgonnadie/salty_bot')

                    elif self.message_body == 'restart' and self.sender in SUPER_USER:
                        if self.__DB:
                            print('{} is restarting, called by {}'.format(self.channel + ' ' + self.twitch_nick, self.sender))
                        self.admin(RESTART)
                        self.twitch_send_message('Restarting the bot.')
                        break

                    elif self.message_body == 'stop' and self.sender in SUPER_USER:
                        if self.__DB:
                            print('SHUTDOWN CALLED BY {}'.format(self.sender.upper()))
                        self.admin(STOP)

                    elif self.message_body == 'check' and self.sender in SUPER_USER:
                        self.admin(CHECK)
                        
                    elif self.message_body == 'crash' and self.sender in SUPER_USER:
                        self.running = False


            elif self.action == 'MODE':
                if '+o ' in self.message:
                    admin = self.message.split('+o ')[-1]
                    if admin not in self.admin_file:
                        with open('{}_admins.txt'.format(self.channel), 'a+') as data_file:
                            data_file.write('{}\n'.format(admin))
                        with open('{}_admins.txt'.format(self.channel), 'a+') as data_file:
                            self.admin_file = data_file.read()

            if self.config_data['general']['social']['text'] != '':
                if self.messages_received >= (self.command_times['social']['messages'] + self.command_times['social']['messages_last']):
                    if int(time.time()) >= ((self.command_times['social']['time'] * 60) + self.command_times['social']['time_last']):
                        self.twitch_send_message(self.social_text)
                        self.command_times['social']['time_last'] = int(time.time())
                        self.command_times['social']['messages_last'] = self.messages_received

        print "thread stoped"
    #@@ ADMIN FUNCTIONS @@#

    def admin(self, call='<test>'):
        if call == RESTART:
            interface.put([call, self])
            if self.__DB:
                print 'bot id {}'.format(self)

        else:
            interface.put([call,self])
    
    def stop(self):
        self.irc.sendall("QUIT")
        self.irc.close()
        
#@@BOT END@@#

def osu_send_message(osu_irc_pass, osu_nick, request_url):
    irc = socket.socket()
    osu_host = 'irc.ppy.sh'
    osu_port = 6667
    irc.connect((osu_host, osu_port))
    irc.sendall('PASS {}\r\n'.format(osu_irc_pass))
    irc.sendall('NICK {}}\r\n'.format(osu_irc_nick))
    irc.sendall('PRIVMSG {} :{}\r\n'.format(osu_nick, request_url))
    irc.close()

def twitch_info_grab(bots):
    with open(Config_file_name, 'r') as data_file:
        channel_configs = json.load(data_file, encoding = 'utf-8')

    channels = channel_configs.keys()
    url = 'https://api.twitch.tv/kraken/streams?channel=' + ','.join(channels)
    headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}
    try:
        data = requests.get(url, headers = headers)
        if data.status_code == 200:
            data_decode = data.json()
            if not data_decode['streams']:
                return
            for i in data_decode['streams']:
                for k, v in bots.iteritems():
                    if i['channel']['name'] == k:
                        v.twitch_info(i['channel']['game'], i['channel']['status'])
    except:
        pass

def restart_bot(bot_name, bot_dict):
    with open(Config_file_name, 'r') as data_file:
        bot_config = json.load(data_file, encoding = 'utf-8')[bot_name]
        
    del bot_dict[bot_name]
    bot_dict[bot_name] = SaltyBot(bot_config, debuging)
    bot_dict[bot_name].start()
        
def automated_main_loop(bot_dict):
    time_to_check = 0
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

        if time_to_check < int(time.time()):
            for bot_name, bot_inst in bot_dict.items():
                if bot_inst.thread.isAlive():
                    if debuging == True:
                        print '#' + bot_name  + ': Is still running'
                    
                else:
                    if debuging == True:
                        print '#' + bot_name + ' Had to restart'
                    restart_bot(bot_inst.channel, bot_dict)
                    
            twitch_info_grab(bot_dict)
            
            time_to_check = int(time.time()) + 60


#@@ BOT MAIN THREAD STRING COMMUNICATION SECTION @@#
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
        
        # Wait because of twitch connect settings
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
