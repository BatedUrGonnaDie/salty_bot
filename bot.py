import requests    #required install module
import socket
import threading
import random
import time
from os.path import exists
from os import remove

loop = 1
limit = 0
game = ''
title = ''
destroy_loop = 0
success = 0
toobou = 1
to = u'\u30c8'
dash = u'\u30FC'
bo = u'\u30DC'
u = u'\u30A6'
base_url = 'https://api.twitch.tv/kraken/'

if exists('login.txt')==True:
    fo = open('login.txt', 'r')
    nick = fo.readline()
    password = fo.readline()
    fo.close()
else:
    fo = open('login.txt', 'w+')
    nick = raw_input('Bot Nick: ')
    print 'Get oauth here (http://www.twitchapps.com/tmi/) if you do\'nt have one'
    password = raw_input('Bot Password (Format:"oauth:xxxxx": ')
    fo.write(nick)
    fo.write('\n')
    fo.write(password)
    fo.close()

#Channel you want the bot on
channel = raw_input('Enter Channel to Gather Info From and Join: ')

irc = socket.socket()
host = 'irc.twitch.tv'
port = 6667

def irc_connect():
    irc.connect((host, port))
    irc.send('PASS ' + password + '\r\n')
    irc.send('NICK ' + nick + '\r\n')
    irc.send('JOIN ' + twitch_channel + '\r\n')

def limiter():  #from Phredd's irc bot
    global limit
    limit = 0
    threading.Timer(30,limiter).start()
limiter()    

def channel_check(channel):
    url = 'https://api.twitch.tv/kraken/streams/'+channel
    headers = {'Accept' : 'application/vnd.twitchtv.v2+json'}
    data = requests.get(url, headers=headers)
    data_decode = data.json()
    if 'error' in data_decode:
        print 'Channel not found'
        global success
        success = 1
    else:
        data_stream = data_decode['stream']
        if data_stream == None:
            print 'Channel Currently Offline'
            success = 0
        else:
            data_channel = data_stream['channel']
            global game
            game = data_stream['game']
            global title
            title = data_channel['status']
            print channel + '\n' + game + '\n' + title
            success = 0

channel_check(channel)
while success == 1:
    channel = raw_input('Enter a Valid Channel: ')
    channel_check(channel)
    
twitch_channel = '#'+channel
raw_input('Hit Enter to Connect to IRC\n')
irc_connect()
time.sleep(2)
initial_messages = irc.recv(1024)
print initial_messages
if initial_messages.find('Login unsuccessful') != -1:
    remove('login.txt')
    irc.close()
    print 'Login was un successful, deleting login file, please try again.'
    raw_input('Hit enter to close this program.\n')
    destroy_loop = 1

while loop == 1:
    if destroy_loop == 1:
        break

    def send_message(response):
        global limit
        limit = limit + 1
        if limit < 20:
            irc.send('PRIVMSG ' + twitch_channel + ' :' + response + '\r\n')
        else:
            print 'Sending to quckly'
    
    messages = irc.recv(4096)
    sender = messages.split('!')[0]
    sender = sender.split(':')[-1]
    message_body = messages.split(':')[-1]
    print messages + '\n'

    if messages.find('jtv MODE #'+channel+' +o') != -1:
        print 'Mode change found.'
        jtv_sender = messages.startswith(':jtv')
        if jtv_sender == True:
            admin_extract = messages.rsplit('+o ')[-1]
            print 'Admin to be added: ' + admin_extract
            fo = open('admins.txt', 'a+')
            admin_file = fo.read()
            fo.close()
            print 'Admins currently on file: ' + admin_file
            if admin_extract in admin_file:
                print 'Admin already in file.'
            else:
                print 'Added to the file.'
                fo = open('admins.txt', 'a')
                fo.write(admin_extract)
                fo.close()
            
    if messages.find('PING') != -1:
        irc.send(messages.replace('PING', 'PONG'))
        print 'Pong\'d'

    if messages.find('!wr') != -1:
        category = messages.split('!wr ')[-1]
##    if messages.find('toobou') != -1:
##        if toobou == 1:
##            response = u'I think you meant ' + to + dash + bo + u
##            #response = response.encoding('utf-8')
##            send_message(response)
##            toobou = 0
##            threading.timer(60).start()
##            toobou = 1

#ideas to add: puns, league lookup

