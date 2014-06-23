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
            print("joining {} as {}".format(self.channel,self.twitch_nick))
        self.irc.connect((self.twitch_host, self.port))
        self.irc.send('PASS {}\r\n'.format(self.twitch_oauth))
        self.irc.send('NICK {}\r\n'.format(self.twitch_nick))
        self.irc.send('JOIN #{}\r\n'.format(self.channel))

    def twitch_commands(self):
        for keys in self.config_data['commands']:
            if self.config_data['commands'][keys]['on'] == 'True':
                self.commands.append(keys)
            if self.config_data['commands'][keys]['admin'] == 'True':
                self.admin_commands.append(keys)
            self.command_times[keys] = {'last' : self.config_data['commands'][keys]['last'], 'limit' : self.config_data['commands'][keys]['limit']}
        self.commands_string = ', '.join(self.commands)
        
        if '!vote' in self.commands:
            self.votes = {}

        if self.config_data['general']['social']['text'] != '':
            self.command_times['social'] = {'time_last' : int(time.time()), 'messages' : self.config_data['general']['social']['messages'],
                                            'messages_last' : self.messages_received, 'time' : self.config_data['general']['social']['time']}
            self.social_text = self.config_data['general']['social']['text']

    def twitch_send_message(self, response, command = ''):
            response = response.encode('utf-8')
            to_send = 'PRIVMSG #{} :{}\r\n'.format(self.channel, response)
            self.irc.sendall(to_send)
            if command != '':
                self.command_times[command]['last'] = int(time.time())

    def time_check(self, command):
        if (int(time.time()) - self.command_times[command]['last']) >= self.command_times[command]['limit']:
            return True
        else:
            return False

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
        if self.game in self.config_data['commands']['!wr']['games']:
            for keys in self.config_data['commands']['!wr']['games'][self.game].keys():
                if keys in self.title:
                    wr = self.config_data['commands']['!wr']['games'][self.game][keys]
                    self.twitch_send_message(wr, '!wr')

    def leaderboard_retrieve(self):
        if self.game in self.config_data['commands']['!leaderboards']['games']:
            leaderboard = self.config_data['commands']['!leaderboards']['games'][self.game]
            self.twitch_send_message(leaderboard, '!leaderboards')
            
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
        lines = sum(1 for line in open('{}_{}.txt'.format(self.channel, text_type), 'a+'))
        with open('{}_{}.txt'.format(self.channel, text_type), 'r') as data_file:
            lines_read = data_file.readlines()
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
                        break
                except: 
                    self.this_retrieve = ''
                    continue
        self.twitch_send_message(response, '!' + text_type)
        self.last_retrieve = self.this_retrieve

    def counter(self):
        pass

    def srl_race_retrieve(self):
        self.srl_nick = self.config_data['general']['srl_nick']
        url = 'http://api.speedrunslive.com/races'
        data = requests.get(url)
        data_decode = data.json()
        data_races = data_decode['races']
        srl_race_entrants = []
        for i in data_races:
            for races in i['entrants']:
                if self.srl_nick in races:
                    race_channel = i
                    for values in race_channel['entrants'].values():
                        srl_race_entrants.append(values['twitch'])
                    user = i['entrants'][self.srl_nick]['twitch']
                    srl_race_game = race_channel['game']['name']
                    srl_race_category = race_channel['goal']
                    srl_race_id = race_channel['id']
                    srl_race_link = 'http://www.speedrunslive.com/race/?id={}'.format(srl_race_id)
                    multitwitch_link = 'www.multitwitch.tv/'
                    if len(srl_race_entrants) <= 6:
                        for i in srl_race_entrants:
                            multitwitch_link += i + '/'
                        response = '{} is racing {} in {}.  {}'.format(user, srl_race_category, srl_race_game, multitwitch_link)
                        self.twitch_send_message(response, '!race')
                    else:
                        response = '{} is racing {} in {}.  {}'.format(user, srl_race_category, srl_race_game, srl_race_link)
                        self.twitch_send_message(response, '!race')

    def youtube_video_check(self, message):
        self.youtube_api_key = self.config_data['general']['youtube_api_key']
        youtube_video_id = message.split('youtube.com/watch?v=')[-1]
        if ' ' in youtube_video_id:
            youtube_video_id = youtube_video_id.split(' ')[0]
        url = 'https://www.googleapis.com/youtube/v3/videos?id={}&key={}&part=snippet,contentDetails,statistics,status'.format(youtube_video_id, self.youtube_api_key)
        data = requests.get(url)
        data_decode = data.json()
        data_items = data_decode['items']
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
                response = 'You did not put an open vote category.'
        self.twitch_send_message(response, '!vote')

    def check_votes(self, message):
        try:
            vote_category = message.split(' ')[1]
            if bool(self.votes[vote_category]['votes']) == False:
                response = 'No one has bet in {} yet.'.format(vote_category)
            else:
                winning_key = max(self.votes[vote_category]['votes'], key = self.votes[vote_category].get)
                winning_value = self.votes[vote_category]['votes'][winning_key]
                response = '{} is winning with {} votes for it.'.format(winning_key, winning_value)
        except IndexError:
            response_list = []
            for categories in self.votes:
                if bool(self.votes[categories]['votes']) != False:
                    winning_key = max(self.votes[categories]['votes'], key = self.votes[categories].get)
                    winning_value = self.votes[categories]['votes'][winning_key]
                    response_list.append('{}: {} is winning with {} votes.'.format(categories, winning_key, winning_value))
            response = '.  '.join(response_list)
        self.twitch_send_message(response, '!vote')

    def twitch_run(self):
        self.twitch_connect()
        self.twitch_commands()
        
        while self.running:
                
            self.message = self.irc.recv(4096)
            self.message = self.message.split('\r\n')[0]
            
            if self.message.startswith('PING'):
                self.irc.send('PONG tmi.twitch.tv\r\n')
                
            try:
                self.action = self.message.split(' ')[1]
            except:
                self.action = ''
                    
            if self.action == 'PRIVMSG':
                self.messages_received += 1
                self.sender = self.message.split(':')[1].split('!')[0]
                self.message_body = ':'.join(self.message.split(':')[2:])

                if self.message_body.find('osu.ppy.sh/b/') != -1 or self.message_body.find('http://osu.ppy.sh/s/') != -1:
                    if self.game == 'osu!':
                        if self.config_data['general']['osu']['song_link'] != 'False':
                            self.osu_link()

                if self.message_body.find('youtube.com/watch?v=') != -1:
                    if self.config_data['general']['youtube_link']:
                        self.youtube_video_check(self.message_body)
                
                if self.__DB:
                    print("message body: " + self.message_body)
                
                if self.message_body.startswith('!'):
                    self.message_body = self.message_body.split('!')[-1]

                    if self.message_body.startswith('wr'):
                        if '!wr' in self.commands:
                            if '!wr' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.wr_retrieve()
                            else:
                                if self.time_check('!wr') == True:
                                    self.wr_retrieve()

                    elif self.message_body.startswith('leaderboard'):
                        if '!leaderboards' in self.commands:
                            if '!leaderboards' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.leaderboard_retrieve()
                            else:
                                if self.time_check('!leaderboards') == True:
                                    self.leaderboard_retrieve()

                    elif self.message_body.startswith('addquote'):
                        if '!quote' in self.commands:
                            if '!qoute' in self.admin_commands:
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
                                if self.time_check('!quote') == True:
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
                                if self.time_check('!pun') == True:
                                    self.text_retrieve('pun')

                    elif self.message_body == 'rank':
                        if self.game == 'osu!':
                            if '!rank' in self.commands:
                                if '!rank' in self.admin_commands:
                                    if self.sender in self.admin_file:
                                        self.osu_api_user()
                                else:
                                    if self.time_check('!rank') == True:
                                        self.osu_api_user()

                    elif self.message_body == 'race':
                        if '!race' in self.commands:
                            if '!race' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    if 'race' in self.title or 'races' in self.title or 'racing' in self.title:
                                        self.srl_race_retrieve()
                            else:
                                if 'race' in self.title or 'races' in self.title or 'racing' in self.title:
                                    if self.time_check('!race') == True:
                                        self.srl_race_retrieve()

                    elif self.message_body.startswith('vote '):
                        if '!vote' in self.commands:
                            if '!vote' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.vote(self.message_body, self.sender)
                            else:
                                if self.time_check('!vote') == True:
                                    self.vote(self.message_body, self.sender)

                    elif self.message_body.startswith('votes'):
                        if '!vote' in self.commands:
                            if '!vote' in self.admin_commands:
                                if self.sender in self.admin_file:
                                    self.check_votes(self.message_body)
                            else:
                                self.check_votes(self.message_body)

                    elif self.message_body == 'commands':
                        if self.time_check('!vote') == True:
                            self.twitch_send_message(self.commands_string, '!commands')

                    elif self.message_body == 'restart' and self.sender == self.channel:# or self.sender == "bomb_mask"):
                        if self.__DB:
                            print('{} is restarting, called by {}'.format(self.channel + ' ' + self.twitch_nick, self.sender))
                        self.admin(RESTART)
                        self.twitch_send_message('Restarting the bot.')

                        break

                    elif 'stop' in self.message_body and (self.sender == 'batedurgonnadie' or self.sender == 'bomb_mask'):
                        if self.__DB:
                            print('SHUTDOWN CALLED BY {}'.format(self.sender.upper()))
                        self.admin(STOP)

                    elif 'check' in self.message_body:
                        self.admin(CHECK)


                elif self.action == 'MODE':
                    if '+o ' in self.message:
                        self.admin = self.message.split('+o ')[-1]
                        if self.admin not in self.admin_file:
                            self.fo = open('{}_admins.txt'.format(self.channel), 'a+')
                            self.fo.write('{}\n'.format(self.admin))
                            self.fo.close()
                            with open('{}_admins.txt'.format(self.channel), 'a+') as data_file:
                                self.admin_file = data_file.read()
                                
            if self.config_data['general']['social']['text'] != '':
                if self.messages_received >= (self.command_times['social']['messages'] + self.command_times['social']['messages_last']):
                    if int(time.time()) >= ((self.command_times['social']['time'] * 60) + self.command_times['social']['time_last']):
                        time.sleep(random.randrange(1, 20, 1))
                        self.twitch_send_message(self.social_text)
                        self.command_times['social']['last_time'] = int(time.time())
                        self.command_times['social']['last_message'] = self.messages_received
                        
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
        url = 'https://api.twitch.tv/kraken/channels/'+channel
        headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}        
        data = requests.get(url, headers = headers)
        data_decode = data.json()
        #data_stream = data_decode['stream']  

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
    
#toobou rate limiting, review quotes/puns from chat
#runes/masteries
#make web page that doesn't suck
