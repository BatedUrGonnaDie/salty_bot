import os
import sys
import time
import random
import threading
import socket
import requests
import ConfigParser

class SaltyBot:
    messages_received = 0

    def __init__(self, config_data):
        self.config_data = config_data
        self.irc = socket.socket()
        self.config_data = config_data
        self.twitch_host = 'irc.twitch.tv'
        self.port = 6667
        self.twitch_nick = config_data['twitch_nick']
        self.twitch_oauth = config_data['twitch_oauth']
        self.osu_nick = config_data['osu_nick']
        self.osu_api_key = config_data['osu_api_key']
        self.channel = config_data['channel']
        self.fo = open('{}_admins.txt'.format(self.channel), 'a+')
        self.fo.close()
        self.fo = open('{}_quotes.txt'.format(self.channel), 'a+')
        self.fo.close()

    def twitch_check(self):
        self.url = 'https://api.twitch.tv/kraken/streams/'+self.channel
        self.headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}
        
        self.data = requests.get(self.url, headers = self.headers)
        self.data_decode = self.data.json()
        self.data_stream = self.data_decode['stream']
        
        if self.data_stream == None:
            self.game = ''
            self.title = ''
            return self.game, self.title
        else:
            self.data_channel = self.data_stream['channel']
            self.game = self.data_stream['game']
            self.title = self.data_channel['status']
            return self.game, self.title

    def osu_api_user(self):
        self.url = 'https://osu.ppy.sh/api/get_user?k={}&u={}'.format(self.osu_api_key, self.osu_nick)
        self.data = requests.get(self.url)
        
        self.data_decode = self.data.json()
        self.data_decode = self.data_decode[0]
        
        self.username = self.data_decode['username']
        self.level = self.data_decode['level']
        self.level = round(float(self.level))
        self.level = int(self.level)
        self.accuracy = self.data_decode['accuracy']
        self.accuracy = round(float(self.accuracy), 2)
        self.pp_rank = self.data_decode['pp_rank']
        
        self.response = '{} is level {} with {}% accuracy and ranked {}.'.format(self.username, self.level, self.accuracy, self.pp_rank)
        self.twitch_send_message(self.response)

    def twitch_connect(self):
        self.irc.connect((self.twitch_host, self.port))
        self.irc.send('PASS {}\r\n'.format(self.twitch_oauth))
        self.irc.send('NICK {}\r\n'.format(self.twitch_nick))
        self.irc.send('JOIN #{}\r\n'.format(self.config_data['channel']))

    def twitch_send_message(self, response):
        self.to_send = 'PRIVMSG #{} :{}\r\n'.format(self.channel, self.response)
        self.to_send = self.to_send.encode('utf-8')
        self.irc.send(self.to_send)
        time.sleep(1.5)

    def twitch_run(self):
        self.game, self.title = self.twitch_check()
        self.twitch_connect()

        while True:
            self.message = self.irc.recv(4096)
            self.message = self.message.split('\r\n')[0]
            #print self.message
            
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
                    
                    if self.message_body.startswith('!'):
                        self.message_body = self.message_body.split('!')[-1]
                        if self.message_body == 'rank':
                            self.osu_api_user()
                            
                    
                elif self.action == 'MODE':
                    if '+o ' in self.message:
                        self.admin = self.message.split('+o ')[-1]
                        self.fo = open('{}_admins.txt'.format(self.channel), 'r')
                        self.admin_file = self.fo.read()
                        self.fo.close()
                        
                        if self.admin not in self.admin_file:
                            self.fo = open('{}_admins.txt'.format(self.channel), 'a+')
                            self.fo.write(self.admin)
                            self.fo.close()



def osu_main(osu_nick, message):
    osu_irc_pass = config.get('General', 'osu_irc_pass')
    irc = socket.socket()
    osu_host = 'irc.ppy.sh'
    osu_port = 6667
    irc.connect((osu_host, osu_port))
    irc.send('PASS {}\r\n'.format(osu_irc_pass))
    irc.send('NICK batedurgonnadie\r\n')
    irc.send('PRIVMSG {}: {}'.format(osu_nick, message))
        
                  
def main():
    #Config reader
    config = ConfigParser.SafeConfigParser()
    config.read('channels.ini')
    
    #Handling arrays
    channel_configs = {}
    bots = []
    
    for section_name in config.sections():
        channel_configs[section_name] = {}
        for name, value in config.items(section_name):
            channel_configs[section_name][name] = value
            channel_configs[section_name]['channel'] = section_name
            config.read('config.ini')
            channel_configs[section_name]['osu_api_key'] = config.get('General', 'osu_api_key')

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
