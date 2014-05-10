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
    message_limit = 0

    def __init__(self, config_data):
        self.irc = socket.socket()
        self.config_data = config_data
        self.twitch_host = 'irc.twitch.tv'
        self.port = 6667
        print config_data
        self.twitch_nick = config_data['twitch_nick']
        self.twitch_oauth = config_data['twitch_oauth']

    def twitch_check(self):
        self.url = 'https://api.twitch.tv/kraken/streams/'+self.twitch_nick
        self.headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}
        self.data = requests.get(self.url, headers = self.headers)
        self.data.decode = self.data.json()
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

    def twitch_run(self):
        self.game, self.title = self.twitch_check()
        print self.game
        print self.title
        self.twitch_connect()

        while True:
            message = self.irc.recv(4096)
            print message
    
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

    while True:
        time.sleep(1)
        

if __name__ == '__main__':
    main()
