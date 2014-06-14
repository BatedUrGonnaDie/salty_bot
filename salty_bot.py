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

class SaltyBot:
    
    def __init__(self, config_data):
        self.config_data = config_data
        self.irc = socket.socket()
        self.twitch_host = 'irc.twitch.tv'
        self.port = 6667
        self.twitch_nick = config_data['general']['twitch_nick']
        self.twitch_oauth = config_data['general']['twitch_oauth']
        self.channel = config_data['general']['channel']
        self.commands = []
        with open('{}_admins.txt'.format(self.channel), 'a+') as data_file:
            self.admin_file = data_file.read()

    def twitch_info(self, info):
        self.game = info[self.channel]['game']
        self.title = info[self.channel]['title']

    def twitch_connect(self):
        self.irc.connect((self.twitch_host, self.port))
        self.irc.send('PASS {}\r\n'.format(self.twitch_oauth))
        self.irc.send('NICK {}\r\n'.format(self.twitch_nick))
        self.irc.send('JOIN #{}\r\n'.format(self.channel))

    def twitch_commands(self):
        for keys in self.config_data['commands']:
            if self.config_data['commands'][keys] != 'False':
                self.commands.append(keys)
        self.commands_string = ', '.join(self.commands)

        
    def twitch_send_message(self, response):
        self.last_response = response
        response = response.encode('utf-8')
        to_send = 'PRIVMSG #{} :{}\r\n'.format(self.channel, response)
        #self.to_send = self.to_send.encode('utf-8')
        self.irc.send(to_send)
        time.sleep(1.5)

    def osu_api_user(self):
        osu_nick = self.config_data['general']['osu']['osu_nick']
        osu_api_key = self.config_data['general']['osu']['osu_api_key']
        url = 'https://osu.ppy.sh/api/get_user?k={}&u={}'.format(osu_api_key, osu_nick)
        data = requests.get(url)
        data_decode = data.json()
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
        osu_irc_pass = self.config_data['general']['osu']['osu_irc_pass']
        osu_api_key = self.config_data['general']['osu']['osu_api_key']
        
        if self.message_body.find('osu.ppy.sh/s/') != -1:
            osu_number = 's=' + self.message_body.split('osu.ppy.sh/s/')[-1].split(' ')[0]
        elif self.message_body.find('osu.ppy.sh/b/') != -1:
            osu_number = 'b=' + self.message_body.split('osu.ppy.sh/b/')[-1].split(' ')[0]

        url = 'https://osu.ppy.sh/api/get_beatmaps?k={}&{}'.format(osu_api_key, osu_number)
        data = requests.get(url)
        data_decode = data.json()
        data_decode = data_decode[0]
        response = '{} - {}, mapped by {}'.format(data_decode['artist'], data_decode['title'], data_decode['creator'])

        self.twitch_send_message(response)
        osu_send_message(osu_irc_pass, osu_nick, self.message_body)

    def wr_retrieve(self):
        game = self.game.lower()
        if game in self.config_data['commands']['!wr']:
            for keys in self.config_data['commands']['!wr'][game].keys():
                if keys in self.title.lower():
                    wr = self.config_data['commands']['!wr'][game][keys]
                    self.twitch_send_message(wr)

    def leaderboard_retrieve(self):
        try:
            game = self.game.lower() 
            if game in self.config_data['commands']['!leaderboards']:
                leaderboard = self.config_data['commands']['!leaderboards'][game]
                self.twitch_send_message(leaderboard)
        except:
            self.twitch_send_message('Something went wrong BibleThump')
            
    def add_text(self, text_type, text_add):
        text = text_add.split('{} '.format(text_type))[-1]
        if text == 'addquote' or text == 'addpun':
            self.twitch_send_message('Please input a {}.'.format(text_type))
        elif self.sender == self.channel:
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
        lines = sum(1 for line in open('{}_{}.txt'.format(self.channel, text_type), 'a+'))
        with open('{}_{}.txt'.format(self.channel, text_type), 'r') as data_file:
            lines_read = data_file.readlines()
        if lines == 0:
            response = 'No {}s have been added.'.format(text_type)
        elif lines == 1:
            response = lines_read[0]
        else:
            try:
                while self.this_retrieve == self.last_retrieve:
                    select_line = random.randrange(1, lines, 1)
                    response = lines_read[select_line]
                    self.this_retrieve = response
            except:
                select_line = random.randrange(1, lines, 1)
                response = lines_read[select_line]
                self.this_retrieve = response
        self.twitch_send_message(response)
        self.last_retrieve = self.this_retrieve

    def pb_hype(self):
        pass

    def srl_race_retrieve(self):
        self.srl_nick = config_data['general']['srl_nick']
        url = 'http://api.speedrunslive.com/races'
        data = requests.get(url)
        data_decode = data.json()
        data_races = data_decode['races']
        srl_race_entrants = []
        for i in data_races:
            for races in i['entrants']:
                if self.srl_nick in races:
                    race_channel = i
                    for racers in race_channel['entrants']:
                        srl_race_entrants.append(racers)
                    user = i['entrants'][self.srl_nick]
                    srl_race_game = race_channel['game']['name']
                    srl_race_category = race_channel['goal']
                    srl_race_id = race_channel['id']
                    srl_race_link = 'http://www.speedrunslive.com/race/?id={}'.format(srl_race_id)
                    multitwitch_link = 'www.multitwitch.tv/'
                    if len(srl_race_entrants) <= 6:
                        for i in srl_race_entrants:
                            multitwitch_link += i + '/'
                        self.twitch_send_message('{} is racing {} in {}.\n{}'.format(user, srl_race_category, srl_race_game, multitwitch_link))
                    else:
                        self.twitch_send_message('{} is racing {} in {}.\n{}'.format(user, srl_race_category, srl_race_game, srl_race_link))
                    

    def twitch_run(self):
        self.twitch_connect()
        self.twitch_commands()
        
        while True:
                
            self.message = self.irc.recv(4096)
            self.message = self.message.split('\r\n')[0]
            
            if self.message.startswith('PING'):
                self.irc.send('PONG tmi.twitch.tv\r\n')
                
            else:
                try:
                    self.action = self.message.split(' ')[1]
                except:
                    self.action = ''
                    
                if self.action == 'PRIVMSG':
                    self.sender = self.message.split(':')[1].split('!')[0]
                    self.message_body = ':'.join(self.message.split(':')[2:])

                    if self.message_body.find('http://osu.ppy.sh/b/') != -1 or self.message_body.find('http://osu.ppy.sh/s/') != -1:
                        if self.game.lower() == 'osu!':
                            if self.config_data['general']['song_link'] != 'False':
                                self.osu_link()
                        
                    if self.message_body.startswith('!'):
                        self.message_body = self.message_body.split('!')[-1]

                        if self.message_body.startswith('wr'):
                            if '!wr' in self.commands:
                                self.wr_retrieve()

                        if self.message_body.startswith('leaderboard'):
                            if '!leaderboards' in self.commands:
                                self.leaderboard_retrieve()

                        if self.message_body.startswith('addquote'):
                            if '!quote' in self.commands:
                                self.add_text('quote', self.message_body)

                        if self.message_body == 'quote':
                            if '!quote'in self.commands:
                                self.text_retrieve('quote')

                        if self.message_body.startswith('addpun'):
                            if '!pun' in self.commands:
                                self.add_text('pun', self.message_body)

                        if self.message_body == 'pun':
                            if '!pun' in self.commands:
                                self.text_retrieve('pun')

                        if self.message_body == 'rank':
                            if self.game.lower() == 'osu!':
                                if '!rank' in self.commands:
                                    self.osu_api_user()

                        if self.message_body == 'race':
                            if '!race' in self.commands:
                                if 'race' in self.title or 'races' in self.title or 'racing' in self.title:
                                    self.srl_race_retrieve()

                        if self.message_body == 'commands':
                            self.twitch_send_message(self.commands_string)
                            
                    
                elif self.action == 'MODE':
                    if '+o ' in self.message:
                        self.admin = self.message.split('+o ')[-1]
                        
                        if self.admin not in self.admin_file:
                            self.fo = open('{}_admins.txt'.format(self.channel), 'a+')
                            self.fo.write('{}\n'.format(self.admin))
                            self.fo.close()
                            with open('{}_admins.txt'.format(self.channel), 'a+') as data_file:
                                self.admin_file = data_file.read()

def osu_send_message(osu_irc_pass, osu_nick, request_url):
    irc = socket.socket()
    osu_host = 'irc.ppy.sh'
    osu_port = 6667
    irc.connect((osu_host, osu_port))
    irc.send('PASS {}\r\n'.format(osu_irc_pass))
    irc.send('NICK batedurgonnadie\r\n')
    irc.send('PRIVMSG {} :{}\r\n'.format(osu_nick, request_url))
    irc.close()

def twitch_info_grab(bots):
    with open('config.json', 'r') as data_file:
        channel_configs = json.load(data_file, encoding = 'utf-8')
    channels = channel_configs.keys()
    channel_game_title = {}
    for channel in channels:
        url = 'https://api.twitch.tv/kraken/streams/'+channel
        headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}
        
        data = requests.get(url, headers = headers)
        data_decode = data.json()
        data_stream = data_decode['stream']
    
        if data_stream == None:
            game = ''
            title = ''
        else:
            data_channel = data_stream['channel']
            game = data_stream['game']
            title = data_channel['status']
        channel_game_title.update({'{}'.format(channel) : {'game' : '{}'.format(game), 'title' : '{}'.format(title)}})
    bots_update = []
    for bot in bots:
        bot.twitch_info(channel_game_title)
        bots_update.append(bot)
    
    t_check = threading.Timer(60, twitch_info_grab, args = [bots_update])
    t_check.daemon = True
    t_check.start()

def main():
    channel_configs = {}
    with open('config.json', 'r') as data_file:
        channel_configs = json.load(data_file, encoding = 'utf-8')

    bots = []
    for channels in channel_configs.values():
        bots.append(SaltyBot(channels))

    for bot in bots:
        tmp = threading.Thread(target=bot.twitch_run)
        tmp.daemon = True
        tmp.start()

    twitch_info_grab(bots)
    
    while True:
        time.sleep(1)
        

if __name__ == '__main__':
    main()
    
#voting, social, toobou rate limiting, review quotes/puns from chat
#add admin checking for each command
#runes/masteries
#make web page that doesn't suck
