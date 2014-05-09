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

    def twitch_connect(self):
        self.irc.connect((self.host, self.port))
        self.irc.send('PASS {password}\r\n'.format(password = self.password))
        self.irc.send('NICK {nick}\r\n'.format(nick = self.nick))

    def twitch_channels(self):
        for i in self.irc_channels:
            irc.send('JOIN {irc}\r\n'.format(irc = self.irc_channels))

    def twitch_run(self):
        self.twitch_connect()
        self.twitch_channels()

        while True:
            message = self.irc.recv(4096)
            print message

def main():
    #Config reader
    config = ConfigParser.SafeConfigParser()
    config.read('channels.ini')
    
    #Handling arrays
    channels = {}
    irc_channels = []
    
    for section_name in config.sections():
        channels[section_name] = {}
        for name, value in config.items(section_name):
            channels[section_name][name] = value
            channels[section_name]['channel'] = section_name
        
    for i in channels.values():
        SaltyBot(channels[i])
    
    
if __name__ == '__main__':
    main()
