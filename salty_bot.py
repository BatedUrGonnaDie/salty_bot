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

debuging = False


RESTART = "<restart>"
STOP = "<stop program>"
CHECK = "<check threads>"

TYPE = 0
DATA = 1

interface = Q.Queue()

class SaltyBot:

    running = True
    messages_received = 0

    def __init__(self, config_data, debug = False):
        self.__DB = debug

        self.config_data = config_data
        self.irc = socket.socket()
        self.twitch_host = 'irc.twitch.tv'
        self.port = 6667
        self.twitch_nick = config_data['general']['twitch_nick']
        self.twitch_oauth = config_data['general']['twitch_oauth']
        self.channel = config_data['general']['channel']
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
        self.thread.daemon = True
        self.thread.start()

        return self.thread

    def twitch_info(self, info):
        self.game = info[self.channel]['game']
        self.title = info[self.channel]['title']

    def twitch_connect(self):
        if self.__DB:
            print("Joining {} as {}.\n".format(self.channel,self.twitch_nick))
        while True:
            try:
                self.irc.connect((self.twitch_host, self.port))
                break
            except:
                print "Connection to {}'s channel failed, attempting to reconnect in 30 seconds.\n".format(self.channel)
                time.sleep(30)
                continue
        self.irc.send('PASS {}\r\n'.format(self.twitch_oauth))
        self.irc.send('NICK {}\r\n'.format(self.twitch_nick))
        self.irc.send('JOIN #{}\r\n'.format(self.channel))

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
            if '!quote' in self.commands:
                self.review = {'quote' : []}
            if '!pun' in self.commands:
                self.review = {'pun' : []}

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

    def time_check(self, command):
        return int(time.time()) - self.command_times[command]['last'] >= self.command_times[command]['limit']

    def is_live(self, user):
        try:
            url = 'https://api.twitch.tv/kraken/streams/' + user
            headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}
            data = requests.get(url, headers = headers)
            data_decode = data.json()
            data_stream = data_decode['stream']
            if data_stream == None:
                return False
            else:
                return True
        except:
            return True

    def osu_api_user(self):
        osu_nick = self.config_data['general']['osu']['osu_nick']
        osu_api_key = self.config_data['general']['osu']['osu_api_key']
        url = 'https://osu.ppy.sh/api/get_user?k={}&u={}'.format(osu_api_key, osu_nick)
        try:
            data = requests.get(url)
            data_decode = data.json()
            data_decode = data_decode[0]
        except:
            return
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
        osu_irc_pass = self.config_data['general']['osu']['osu_irc_pass']
        osu_api_key = self.config_data['general']['osu']['osu_api_key']

        if self.message_body.find('osu.ppy.sh/s/') != -1:
            osu_number = 's=' + self.message_body.split('osu.ppy.sh/s/')[-1].split(' ')[0]
        elif self.message_body.find('osu.ppy.sh/b/') != -1:
            osu_number = 'b=' + self.message_body.split('osu.ppy.sh/b/')[-1].split(' ')[0]

        url = 'https://osu.ppy.sh/api/get_beatmaps?k={}&{}'.format(osu_api_key, osu_number)
        try:
            data = requests.get(url)
            data_decode = data.json()
            data_decode = data_decode[0]
        except:
            return
        response = '{} - {}, mapped by {}'.format(data_decode['artist'], data_decode['title'], data_decode['creator'])

        self.twitch_send_message(response)
        osu_send_message(osu_irc_pass, osu_nick, self.message_body)

    def wr_retrieve(self):
        if self.game in self.config_data['commands']['!wr']['games']:
            for keys in self.config_data['commands']['!wr']['games'][self.game].keys():
                if keys in self.title:
                    wr = self.config_data['commands']['!wr']['games'][self.game][keys]
                    self.twitch_send_message(wr, '!wr')

    def leaderboard_retrieve(self):
        if self.game in self.config_data['commands']['!leaderboard']['games']:
            leaderboard = self.config_data['commands']['!leaderboard']['games'][self.game]
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
        try:
            data = requests.get(url)
            data_decode = data.json()
            data_races = data_decode['races']
        except:
            return
        srl_race_entrants = []
        for i in data_races:
            for races in i['entrants']:
                if self.srl_nick in races:
                    race_channel = i
                    for values in race_channel['entrants'].values():
                        if values['statetext'] == 'Ready':
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
        self.youtube_api_key = self.config_data['general']['youtube_api_key']
        url_values = urlparse.parse_qs(urlparse.urlparse(message).query)
        youtube_video_id = url_values['v'][0]
        if ' ' in youtube_video_id:
            youtube_video_id = youtube_video_id.split(' ')[0]
        url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={}&key={}'.format(youtube_video_id, self.youtube_api_key)
        try:
            data = requests.get(url)
            data_decode = data.json()
            data_items = data_decode['items']
        except:
            return
        youtube_title = data_items[0]['snippet']['title']
        youtube_uploader = data_items[0]['snippet']['channelTitle']
        response = '{} uploaded by {}'.format(youtube_title, youtube_uploader)
        self.twitch_send_message(response)

    def vote(self, message, sender):
        vote_category = message.split(' ')[1]
        if vote_category == 'createvote':
            if self.sender == self.channel or self.sender in self.admin_file:
                vote_section = message.split('createvote ')[-1]
                self.votes[vote_section] = {}
                self.votes[vote_section]['votes'] = {}
                self.votes[vote_section]['voters'] = {}
                response = 'You can now vote for {}.'.format(vote_section)
            else:
                response = 'You do not have permission to do that.'
        elif vote_category == 'removevote':
            if self.sender == self.channel or self.sender in self.admin_file:
                vote_section = message.split('removevote ')[-1]
                if vote_section in self.votes:
                    try:
                        winning_key = max(self.votes[vote_section]['votes'], key = self.votes[vote_section].get)
                        winning_value = self.votes[vote_section]['votes'][winning_key]
                        del self.votes[vote_section]
                        response = '{} can no longer be voted on anymore.  {} has won with {} votes.'.format(vote_section, winning_key, str(winning_value))
                    except ValueError:
                        del self.votes[vote_section]
                        response = ''
            else:
                response = 'You do not have permission to do that.'
        else:
            if vote_category in self.votes:
                sender_bet = message.split(vote_category)[-1]
                sender_bet = sender_bet[1:]
                if sender in self.votes[vote_category]['voters'] and sender_bet == self.votes[vote_category]['voters'][sender]:
                    pass
                elif sender in self.votes[vote_category]['voters'] and sender_bet != self.votes[vote_category]['voters'][sender]:
                    previous_bet = self.votes[vote_category]['voters'][sender]
                    self.votes[vote_category]['votes'][previous_bet] -= 1
                    if self.votes[vote_category]['votes'][previous_bet] == 0:
                        del self.votes[vote_category]['votes'][previous_bet]
                    if sender_bet in self.votes[vote_category]['votes']:
                        self.votes[vote_category]['votes'][sender_bet] += 1
                    else:
                        self.votes[vote_category]['votes'][sender_bet] = 1
                    self.votes[vote_category]['voters'][sender] = sender_bet
                    response = 'Your vote has been recorded.'
                else:
                    if sender_bet in self.votes[vote_category]['votes']:
                        self.votes[vote_category]['votes'][sender_bet] += 1
                    else:
                        self.votes[vote_category]['votes'][sender_bet] = 1
                    self.votes[vote_category]['voters'][sender] = sender_bet
                    response = 'Your vote has been recorded.'
            else:
                return
        self.twitch_send_message(response, '!vote')

    def check_votes(self, message):
        try:
            vote_category = message.split(' ')[1]
            if not self.votes[vote_category]['votes']:
                response = 'No one has bet in {} yet.'.format(vote_category)
            else:
                winning_key = max(self.votes[vote_category]['votes'], key = self.votes[vote_category].get)
                winning_value = self.votes[vote_category]['votes'][winning_key]
                response = '{} is winning with {} votes for it.'.format(winning_key, winning_value)
        except IndexError:
            response_list = []
            for categories in self.votes:
                if self.votes[categories]['votes']:
                    winning_key = max(self.votes[categories]['votes'], key = self.votes[categories].get)
                    winning_value = self.votes[categories]['votes'][winning_key]
                    response_list.append('{}: {} is winning with {} votes.'.format(categories, winning_key, winning_value))
            response = '.  '.join(response_list)
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

    def twitch_run(self):
        self.twitch_connect()
        self.twitch_commands()

        while self.running:

            self.message = self.irc.recv(4096)
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

                find_ex = self.message_body.count('!')
                if self.message_body.startswith('!'):
                    self.message_body = self.message_body.split('!')[-find_ex]

                    if self.message_body.startswith('blacklist ') and self.sender == self.channel:
                        self.lister(self.message_body, 'black')

                    elif self.message_body.startswith('whitelist ') and self.sender == self.channel:
                        self.lister(self.message_body, 'white')

                    elif self.message_body.startswith('wr'):
                        if '!wr' in self.commands:
                            if '!wr' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.wr_retrieve()
                            else:
                                if self.time_check('!wr'):
                                    self.wr_retrieve()

                    elif self.message_body.startswith('leaderboard'):
                        if '!leaderboard' in self.commands:
                            if '!leaderboard' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.leaderboard_retrieve()
                            else:
                                if self.time_check('!leaderboard'):
                                    self.leaderboard_retrieve()

                    elif self.message_body.startswith('addquote'):
                        if '!quote' in self.commands:
                            if '!quote' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.add_text('quote', self.message_body)
                            else:
                                self.add_text('quote', self.message_body)

                    elif self.message_body == 'quote':
                        if '!quote'in self.commands:
                            if '!quote' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.text_retrieve('quote')
                            else:
                                if self.time_check('!quote'):
                                    self.text_retrieve('quote')

                    elif self.message_body.startswith('addpun'):
                        if '!pun' in self.commands:
                            if '!pun' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.add_text('pun', self.message_body)
                            else:
                                self.add_text('pun', self.message_body)

                    elif self.message_body == 'pun':
                        if '!pun' in self.commands:
                            if '!pun' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.text_retrieve('pun')
                            else:
                                if self.time_check('!pun'):
                                    self.text_retrieve('pun')

                    elif self.message_body == 'rank':
                        if self.game == 'osu!':
                            if '!rank' in self.commands:
                                if '!rank' in self.admin_commands:
                                    if self.sender in self.admin_file:
                                        self.osu_api_user()
                                else:
                                    if self.time_check('!rank'):
                                        self.osu_api_user()

                    elif self.message_body == 'race':
                        if '!race' in self.commands:
                            if '!race' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    if 'race' in self.title or 'races' in self.title or 'racing' in self.title:
                                        self.srl_race_retrieve()
                            else:
                                if 'race' in self.title or 'races' in self.title or 'racing' in self.title:
                                    if self.time_check('!race'):
                                        self.srl_race_retrieve()

                    elif self.message_body.startswith('vote '):
                        if '!vote' in self.commands:
                            if '!vote' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.vote(self.message_body, self.sender)
                            else:
                                if self.time_check('!vote'):
                                    self.vote(self.message_body, self.sender)

                    elif self.message_body.startswith('votes'):
                        if '!vote' in self.commands:
                            if '!vote' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.check_votes(self.message_body)
                            else:
                                if self.time_check('!vote'):
                                    self.check_votes(self.message_body)

                    elif self.message_body in self.command_times['custom']['triggers']:
                        location = self.command_times['custom']['triggers'].index(self.message_body)
                        if int(time.time()) - self.command_times['custom']['lasts'][location] >= self.command_times['custom']['limits'][location]:
                            if self.message_body in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.twitch_send_message(self.command_times['custom']['outputs'][location])
                            else:
                                self.twitch_send_message(self.command_times['custom']['outputs'][location])
                                self.command_times['custom']['lasts'][location] = int(time.time())

                    elif self.message_body.startswith('review') and self.sender == self.channel:
                        self.text_review(self.message_body)

                    elif self.message_body == 'commands':
                        if self.time_check('!commands'):
                            self.twitch_send_message(self.commands_string, '!commands')

                    elif self.message_body == 'restart' and self.sender == self.channel:# or self.sender == "bomb_mask"):
                        if self.__DB:
                            print('{} is restarting, called by {}'.format(self.channel + ' ' + self.twitch_nick, self.sender))
                        self.admin(RESTART)
                        self.twitch_send_message('Restarting the bot.')
                        break

                    elif self.message_body == 'stop' and (self.sender == 'batedurgonnadie' or self.sender == 'bomb_mask'):
                        if self.__DB:
                            print('SHUTDOWN CALLED BY {}'.format(self.sender.upper()))
                        self.admin(STOP)

                    elif self.message_body == 'check':
                        self.admin(CHECK)


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

        print("thread stoped")
    #@@ ADMIN FUNCTIONS @@#

    def admin(self,call='<test>'):
        if call == RESTART:
            interface.put([call,self])
            if self.__DB:
                print('bot id {}'.format(self))

        else:
            interface.put([call,self])

#@@BOT END@@#

def osu_send_message(osu_irc_pass, osu_nick, request_url):
    irc = socket.socket()
    osu_host = 'irc.ppy.sh'
    osu_port = 6667
    irc.connect((osu_host, osu_port))
    irc.sendall('PASS {}\r\n'.format(osu_irc_pass))
    irc.sendall('NICK batedurgonnadie\r\n')
    irc.sendall('PRIVMSG {} :{}\r\n'.format(osu_nick, request_url))
    irc.close()

def twitch_info_grab(bots):
    with open('config.json', 'r') as data_file:
        channel_configs = json.load(data_file, encoding = 'utf-8')

    channels = channel_configs.keys()
    channel_game_title = {}

    for channel in channels:
        url = 'https://api.twitch.tv/kraken/channels/'+channel
        headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}
        try:
            data = requests.get(url, headers = headers)
            data_decode = data.json()
        except:
            data_decode = {'game' : '', 'status' : ''}

        game = data_decode['game']
        title = data_decode['status']

        try:
            game = game.lower()
        except:
            game = ''
        try:
            title = title.lower()
        except:
            title = ''

        channel_game_title.update({channel : {'game' : game, 'title' : title}})

    bots_update = []

    for bot in bots:
        bot.twitch_info(channel_game_title)
        bots_update.append(bot)

    t_check = threading.Timer(60, twitch_info_grab, args = [bots_update])
    t_check.daemon = True
    t_check.start()

def restartBot(bot,bot_list):
    #@ OPEN CONFIGURATION FILE
    with open('config.json', 'r') as data_file:
        #@ GET THE RIGHT CONFIG DICTIONARY FROM THE FILE
        bot_config = json.load(data_file, encoding = 'utf-8')[bot.channel]

    # FIND THE BOT IN THE LIST USING INDEX
    bot_location = bot_list.index(bot)
    # DELETE THE OLD BOT AND REPLACE THE POSISTION IN THE LIST WITH THE RESTARTED BOT
    bot_list[bot_location] = SaltyBot(bot_config, debuging)
    # START THE THREAD AGAIN ON THE NEW BOT
    bot_list[bot_location].start()


#@@ BOT MAIN THREAD STRING COMMUNICATION SECTION @@#


def main():
    running = True

    channel_configs = {}
    with open('config.json', 'r') as data_file:
        channel_configs = json.load(data_file, encoding = 'utf-8')

    bots = []
    for channels in channel_configs.values():
        #@@ CREATE BOT INSTANCE @@#
        bots.append(SaltyBot(channels, debuging))
        #@@ START BOT THREAD @@#
        bots[-1].start()

    twitch_info_grab(bots)

    ##MAIN LOOP##
    while running:

        try:
            register = interface.get(False)

            if register[TYPE] == RESTART:
                restartBot(register[DATA],bots)

            if register[TYPE] == STOP:
                break

            if register[TYPE] == CHECK:
                for i in bots:
                    print i.thread

        except:
            pass




if __name__ == '__main__':
    main()
    print "program ending"

#runes/masteries
#make web page that doesn't suck
