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
    messages_received = 0

    def __init__(self, config_data):
        self.config_data = config_data
        self.irc = socket.socket()
        self.twitch_host = 'irc.twitch.tv'
        self.port = 6667
        self.twitch_nick = config_data['twitch_nick']
        self.twitch_oauth = config_data['twitch_oauth']
        self.channel = config_data['channel']
        with open('{}_admins.txt'.format(self.channel), 'a+') as data_file:
            self.admin_file = data_file.read()

    def twitch_check(self):
        url = 'https://api.twitch.tv/kraken/streams/'+self.channel
        headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}
        
        data = requests.get(url, headers = headers)
        data_decode = data.json()
        data_stream = data_decode['stream']
        
        if data_stream == None:
            self.game = ''
            self.title = ''
        else:
            self.data_channel = self.data_stream['channel']
            self.game = self.data_stream['game']
            self.title = self.data_channel['status']

    def twitch_connect(self):
        self.irc.connect((self.twitch_host, self.port))
        self.irc.send('PASS {}\r\n'.format(self.twitch_oauth))
        self.irc.send('NICK {}\r\n'.format(self.twitch_nick))
        self.irc.send('JOIN #{}\r\n'.format(self.config_data['channel']))

    def twitch_send_message(self, response):
        response = response.encode('utf-8')
        to_send = 'PRIVMSG #{} :{}\r\n'.format(self.channel, response)
        #self.to_send = self.to_send.encode('utf-8')
        self.irc.send(to_send)
        time.sleep(1.5)

    def osu_api_user(self):
        osu_nick = self.config_data['osu_nick']
        osu_api_key = self.config_data['osu']['osu_api_key']
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

    def wr_retrieve(self):
        if self.game in self.config_data['!wr']:
            for keys in self.config_data['!wr'][self.game].keys():
                if keys in self.title.lower():
                    wr = self.config_data['!wr'][self.game][keys]
                    self.twitch_send_message(wr)

    def leaderboard_retrieve(self):
        try:
            self.game = self.game.lower()
            if self.game in self.config_data['!leaderboards']:
                leaderboard = self.config_data['!leaderboards'][self.game.lower()]
                self.twitch_send_message(leaderboard)
        except:
            self.twitch_send_message('Something went wrong BibleThump')
            

    def add_text(self, text_type, text_add):
        text = text_add.split('{} '.format(text_type))[-1]
        if self.text == 'addquote':
            self.twitch_send_message('Please input a {}.'.format(text_type))
        else:
            with open('{}_{}.txt'.format(self.channel, text_type), 'a+') as data_file:
                data_file.write('{}\n'.format(text))
            response = 'Your {} has been added for review.'.format(text_type)
            self.twitch_send_message(response)

    def text_retrieve(self, text_type):
        lines = sum(1 for line in open('{}_{}.txt'.format(self.channel, text_type), 'w+'))
        with open('{}_{}.txt'.format(self.channel, text_type), 'r') as data_file:
            lines_read = data_file.readlines()
        if lines == 0:
            response = 'No {}s have been added.'.format(text_type)
        elif lines == 1:
            response = lines_read
        else:
            select_line = random.randrange(1, lines, 1)
            response = lines_read[select_line]
        self.twitch_send_message(response)

    def pb_hype(self):
        pass

    def twitch_run(self):
        self.twitch_check()
        self.twitch_connect()
            
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
                    self.messages_received += 1

                    if self.message_body.find('http://osu.ppy.sh/b/') != -1 or self.message_body.find('http://osu.ppy.sh/s/') != -1:
                        if self.game.lower() == 'osu!':
                            if self.config_data['osu'] != 'False':
                                self.osu_nick = self.config_data['osu_nick']
                                self.osu_irc_pass = self.config_data['osu']['osu_irc_pass']
                                osu_send_message(self.osu_irc_pass, self.osu_nick, self.message_body)
                        
                    if self.message_body.startswith('!'):
                        self.message_body = self.message_body.split('!')[-1]

                        if self.message_body.startswith('wr'):
                            if self.config_data['!wr'] != 'False':
                                self.wr_retrieve()

                        if self.message_body.startswith('leaderboard'):
                            if self.config_data['!leaderboards'] != 'False':
                                self.leaderboard_retrieve()

                        if self.message_body.startswith('addquote'):
                            if self.config_data['!quote'] == 'True':
                                self.add_text('quote', self.message_body)

                        if self.message_body == 'quote':
                            if self.config_data['!quote'] == 'True':
                                self.text_retrieve('quote')

                        if self.message_body.startswith('addpun'):
                            if self.config_data['!pun'] == 'True':
                                self.add_text('pun', self.message_body)

                        if self.message_body == 'pun':
                            if self.config_data['!pun'] == 'True':
                                self.text_retrieve('pun')

                        if self.game.lower() == 'osu!':
                            if self.config_data['osu'] != 'False':
                                if self.message_body == 'rank':
                                    self.osu_api_user()

                        if self.message_body == 'recheck' and self.sender in self.admin_file or self.sender == self.channel:
                            self.game, self.title = self.twitch_check()
                            
                    
                elif self.action == 'MODE':
                    if '+o ' in self.message:
                        self.admin = self.message.split('+o ')[-1]
                        
                        if self.admin not in self.admin_file:
                            self.fo = open('{}_admins.txt\n'.format(self.channel), 'a+')
                            self.fo.write(self.admin)
                            self.fo.close()

def osu_send_message(osu_irc_pass, osu_nick, request_url):
    irc = socket.socket()
    osu_host = 'irc.ppy.sh'
    osu_port = 6667
    irc.connect((osu_host, osu_port))
    irc.send('PASS {}\r\n'.format(osu_irc_pass))
    irc.send('NICK batedurgonnadie\r\n')
    irc.send('PRIVMSG {} :{}\r\n'.format(osu_nick, request_url))
    irc.close()
    
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
    
    while True:
        time.sleep(1)
        

if __name__ == '__main__':
    main()
