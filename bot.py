# -*- coding: utf8 -*-
import requests    #required install module
import socket
import threading
import Queue
import random
import time
import sys
import os

loop = 1
limit = 0
game = ''
title = ''
category = ''
wr_time = ''
quote = ''
previous_quote = ''
destroy_loop = 0
success = 0
toobou = 1
base_twitch_url = 'https://api.twitch.tv/kraken/'
base_league_url = 'https://prod.api.pvp.net'

if os.path.exists('login.txt') == True:
    fo = open('login.txt', 'r')
    nick = fo.readline()
    password = fo.readline()
    fo.close()
else:
    fo = open('login.txt', 'w+')
    nick = raw_input('Bot Nick: ')
    print 'Get oauth here (http://www.twitchapps.com/tmi/) if you don\'t have one'
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
    irc.send('JOIN ' + irc_channel + '\r\n')

def limiter():  #from Phredd's irc bot
    global limit
    limit = 0
    threading.Timer(30,limiter).start()
limiter()

def toobou_limiter():
    global toobou
    toobou = 1

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
            game = data_stream['game'].lower()
            global title
            title = data_channel['status'].lower()
            print channel + '\n' + game + '\n' + title
            global category
            if title.find('any%') != -1:
                category = 'any%'
            elif title.find('100%') != -1:
                category = '100%'
            else:
                category = raw_input('Enter a category: ')
            category = category.lower()
            print category
            success = 0

channel_check(channel)
while success == 1:
    channel = raw_input('Enter a Valid Channel: ')
    channel_check(channel)

irc_channel = '#'+channel
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
            to_send = u'PRIVMSG ' + irc_channel + u' :' + response + u'\r\n'
            to_send = to_send.encode('utf-8')
            irc.send(to_send)
        else:
            print 'Sending to quckly'

    def quote_retrieve():
        global quote
        quote_lines = sum(1 for line in open('quotes.txt', 'r'))
        if quote_lines == 0:
            quote = 'No quotes added.'
        elif quote_lines == 1:
            quote = open('quotes.txt', 'r').readline()
        else:
            select_quote = random.randrange(1, quote_lines, 1)
            quote = open('quotes.txt', 'r').readlines()
            quote = quote[select_quote]
    
    messages = irc.recv(4096)
    sender = messages.split('!')[0]
    sender = sender.split(':')[-1]
    message_body = messages.split(':')[-1]
    print sender + ': ' + message_body

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
        if game == 'super mario sunshine':
            if category == 'any%':
                wr_time = u'1:19:34 by トーボウ'
            if category == '100%' or category == '120 shines':
                wr_time = u'3:25:27 by stelzig'
        send_message(wr_time)
        
    if messages.find('!leaderboards') != -1:
        if game == 'super mario sunshine':
            if category == 'any%':
                response = 'http://www.bomch.us/Gw'
            if category == '120 shines' or category == '100%':
                response = 'http://bombch.us/HB'
            send_message(response)

    if messages.find('!addquote') != -1:
        quote = message_body
        quote = quote.split('!addquote ')[-1]
        fo = open('quotes review.txt', 'a+')
        fo.write(quote)
        fo.close()
        response = 'Quote has been added to review list.'
        send_message(response)

    if messages.find('!quote') != -1:
        while previous_quote == quote:
            quote_retrieve()
        send_message(quote)
        previous_quote = quote

    if messages.find('toobou') != -1:
        if toobou == 1:
            response = u'I think you mean トーボウ, #learnmoonrunes'
            send_message(response)
            toobou = 0
            threading.Timer(60,toobou_limiter).start()

    if messages.find('!song') != -1:
        if game == 'osu!':
            np_song = 'np.txt' #have osu!np output to folder bot.py is in
            if os.path.exists(np_song) == True:
                fo = open(np_song, 'r')
                song = fo.read()
                response = 'Currently playing : ' + song
                fo.close()
                send_message(response)
        else:
            np_song = 'current_song.txt'
            if os.path.exists(np_song) == True:
                fo = open(np_song, 'r')
                song = fo.read()
                if song != '':
                    response = 'Currently listening to : ' + song
                    fo.close()
                    send_message(response)
                else:
                    response = 'Not currently listening to anything.'
                    send_message(response)

    if messages.find('!recheck') != -1 and sender == channel:
        channel_check(channel)

    if messages.find('!restart') != -1 and sender == channel:
        pass

    if messages.find('!exit') != -1 and sender == channel:
        irc.close()
        raw_input('Closing down.  Hit enter to conitnue.\n')
        loop = 2
        sys.exit()

#ideas to add: puns, league lookup

