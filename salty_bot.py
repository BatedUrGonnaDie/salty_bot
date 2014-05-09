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
        self.host = 'irc.twitch.tv'
        self.port = 6667
        self.twitch_nick = config_data['twitch_nick']
        self.twitch_oauth = config_data['twitch_oauth']
        print self.host

    def twitch_connect(self):
        print self.host
        print self.port
        self.irc.connect((self.host, self.port))
        self.irc.send('PASS {}\r\n'.format(self.twitch_password))
        self.irc.send('NICK {}\r\n'.format(self.twitch_nick))

    def twitch_run(self):
        self.twitch_connect()

        while True:
            message = self.irc.recv(4096)
            print message

def main():
    #Config reader
    config = ConfigParser.SafeConfigParser()
    config.read('channels.ini')
    
    #Handling arrays
    channels = {}
    bots = []
    
    for section_name in config.sections():
        channels[section_name] = {}
        for name, value in config.items(section_name):
            channels[section_name][name] = value
            channels[section_name]['channel'] = section_name
        
    for channels in channels.values():
        bots.append(SaltyBot(channels))
        
    for bot in bots:
        tmp = threading.Thread(target=bot.twitch_run)
        tmp.daemon = True
        tmp.start()

    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
