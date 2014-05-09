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

    def __init__(self):
        self.irc = socket.socket()

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
    print config.read('channels.ini')
    
    #Handling arrays
    channels = []
    irc_channels = []
    
    for section_name in config.sections():
        channels.append(section_name)
        print section_name
        for name, value in config.items(section_name):
            print '{} = {}'.format(name,value)
        
    for channel in channels:
        irc_channels.append('#'+channel)
    '''
    config.read('config.ini')
    base_configure = {}
    
    base_configure['twitch_nick'] = config.get('Login', 'twitch_nick')
    base_configure['twitch_oauth'] = config.get('Login', 'oauth')
    
    base_configure['osu_nick'] = config.get('Login', 'osu_nick')
    base_configure['osu_pass'] = config.get('Login', 'osu_pass')

    for channel in irc_channels:
        SaltyBot.twitch_run()#OKAY HERE WAS YOUR PROBLEM, YOU DIDN'T CALL THE COMMAND, YOU NEEDED THE '()' ALSO 
    '''
    
if __name__ == '__main__':
    main()
