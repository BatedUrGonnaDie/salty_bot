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
        self.channel_config = self.config_reader(self.config_data)
        self.irc = socket.socket()
        self.config_data = config_data
        self.twitch_host = 'irc.twitch.tv'
        self.port = 6667
        self.twitch_nick = config_data['twitch_nick']
        self.twitch_oauth = config_data['twitch_oauth']
        self.channel = config_data['channel']
        self.fo = open('{}_admins.txt'.format(self.channel), 'a+')
        self.fo.close()
        self.fo = open('{}_quotes.txt'.format(self.channel), 'a+')
        self.fo.close()
    def config_reader(self, initial_config):
        pass

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

    def twitch_connect(self):
        self.irc.connect((self.twitch_host, self.port))
        self.irc.send('PASS {}\r\n'.format(self.twitch_oauth))
        self.irc.send('NICK {}\r\n'.format(self.twitch_nick))
        self.irc.send('JOIN #{}\r\n'.format(self.config_data['channel']))

    def send_message(self, response):
        self.to_send = 'PRIVMSG #{} :{}\r\n'.format(self.channel, self.response)
        self.to_send = self.to_send.encode('utf-8')
        self.irc.send(to_send)
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


def osu_main():
    osu_host = 'irc.ppy.sh'
    osu_port = 6667
    irc = socket.socket()
    irc.connect((osu_host, osu_port))
    irc.send('PASS {}\r\n'.format(osu_irc_pass))
    irc.send('NICK batedurgonnadie\r\n')
    while True:
        messages = irc.recv(4096)
        messages = messages.split('\r\n')[0]
        if messages.startswith('PING'):
            irc.send('PONG irc.ppy.sh')
    
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

    for channels in channel_configs.values():
        bots.append(SaltyBot(channels))

    for bot in bots:
        tmp = threading.Thread(target=bot.twitch_run)
        tmp.daemon = True
        tmp.start()
    t1 = threading.Thread(target = osu_main)
    t1.daemon = True
    t1.start()
    while True:
        time.sleep(1)
        

if __name__ == '__main__':
    main()
