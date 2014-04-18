#! /usr/bin/python2.7
# -*- coding: utf8 -*-

import requests    #required install module
import socket
import threading
import Queue
import random
import time
import sys
import os

import xml.etree.ElementTree as ET
#from salty_bot import *
import ConfigParser
from var import *

##Functions
def file_check(name):
    file_name = name + '.txt'
    if not os.path.exists(file_name):
        fo = open(file_name, 'w')
        fo.close()
        print file_name + ' created.'

def configure():
    if os.path.exists('config.ini'):
        config.read('config.ini')
        twitch_api = config.getboolean("API's", 'Twitch')
        league_api = config.getboolean("API's", 'League')
        osu_api = config.getboolean("API's", 'Osu')
    else:
        print "You will need API keys for each API you wish to use."
        print "Note the basic Twitch info grab does not require an API key."
        twitch_api = raw_input('Use twitch api? y/n: ')
        twitch_api.lower()
        while twitch_api != 'y' and twitch_api != 'n':
            print "Please enter 'y' or 'n'."
            twitch_api = raw_input('Use twitch api? y/n: ')
            twitch_api.lower()
        league_api = raw_input('Use league api? y/n :')
        league_api.lower()
        while league_api != 'y' and league_api != 'n':
            print "Please enter 'y' or 'n'."
            league_api = raw_input('Use league api? y/n: ')
            league_api.lower()
        osu_api = raw_input('Use osu api? y/n: ')
        osu_api.lower()
        while osu_api != 'y' and osu_api != 'n':
            print "Please enter 'y' or 'n'."
            osu_api = raw_input('Use osu api? y/n: ')
            osu_api.lower()
        def boolify(api):
            if api == 'y':
                return True
            elif api == 'n':
                return False
        twitch_api = boolify(twitch_api)
        league_api = boolify(league_api)
        osu_api = boolify(osu_api)
        config.add_section("API's")
        config.add_section('Logins')
        config.set("API's", 'Twitch', twitch_api)
        config.set("API's", 'League', league_api)
        config.set("API's", 'Osu', osu_api)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

def login_io():
    if os.path.exists('login.txt') == True:
        fo = open('login.txt', 'r')
        nick = fo.readline()
        nick = nick.split('\n')[0]
        password = fo.readline()
        password = password.split('\n')[0]
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
    return nick,password

def irc_connect(host,port,nick,password,channel):

    print "Connecting to channel: {channel}\nOn IRC server: {server}\nOn port: {port}\nWith Name: {name}"\
    .format(channel=channel,server=host,port=port,name=nick)

    irc.connect((host, port))
    irc.send('PASS ' + password + '\r\n')
    irc.send('NICK ' + nick + '\r\n')
    irc.send('JOIN ' + channel + '\r\n')

def limiter():  #from Phredd's irc bot
    global limit
    limit = 0
    t1 = threading.Timer(30,limiter)
    t1.daemon = True
    t1.start()

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
        return False
    else:
        data_stream = data_decode['stream']
        if data_stream == None:
            print 'Channel Currently Offline'
            return True
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
            return True

def send_message(response):
    global limit
    limit = limit + 1
    if limit < 20:
        to_send = u'PRIVMSG ' + irc_channel + u' :' + response + u'\r\n'
        to_send = to_send.encode('utf-8')
        irc.send(to_send)
        print nick + ': ' + response
    else:
        print 'Sending to quckly'

def quote_retrieve():
    file_name = 'quotes'
    file_check(file_name)
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

def pun_retrieve():
    file_name = 'puns'
    file_check(file_name)
    global pun
    pun_lines = sum(1 for line in open('puns.txt', 'r'))
    if pun_lines == 0:
        pun = 'No puns added.'
    elif pun_lines == 1:
        pun = open('puns.txt', 'r').readline()
    else:
        select_pun = random.randrange(1, pun_lines, 1)
        pun = open('puns.txt', 'r').readlines()
        pun = pun[select_pun]



##Main Program
nick, password = login_io()

channel = raw_input('Enter Channel to Join: ')

irc = socket.socket()
host = 'irc.twitch.tv'
port = 6667

limiter()
config = ConfigParser.RawConfigParser()
configure()

if channel[0] == '#':
    channel = channel[1:]
irc_channel = '#' + channel

while not channel_check(channel):
    channel = raw_input('Enter a Valid Channel: ')
    channel_check(channel)

raw_input('Hit Enter to Connect to IRC\n')
irc_connect(host,port,nick, password,irc_channel)
time.sleep(2)
initial_messages = irc.recv(1024)

print initial_messages

if initial_messages.find('Login unsuccessful') != -1:
    os.remove('login.txt')
    irc.close()
    print 'Login was un successful, deleting login file, please try again.'
    raw_input('Hit enter to close this program.\n')
    destroy_loop = 1

while loop == 1 and not destroy_loop:

    messages = irc.recv(4096)
    messages = messages.split('\r\n')[0]
    messages = messages.lower()

    try:
        sender = messages.split(":")[1].split("!")[0]
    except IndexError:
        print messages
    try:
        message_body = ":".join(messages.split(":")[2:])
    except IndexError:
        pass
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
            
    if messages.find('PING tmi.twitch.tv') != -1:
        pong = 'PONG tmi.twitch.tv\r\n'
        irc.send(pong)
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

    if messages.find('!addpun') != -1:
        pun = message_body
        pun = pun.split('!addpun ')[-1]
        fo = open('puns review.txt', 'a+')
        fo.write(quote)
        fo.close()
        response = 'Pun has been added to review list.'
        send_message(response)

    if messages.find('!pun') != -1:
        while previous_pun == pun:
            pun_retrieve()
        previous_quote = pun
        send_message(pun)

    if messages.find('toobou') != -1:
        if toobou == 1:
            response = u'I think you mean トーボウ, #learnmoonrunes'
            toobou = 0
            t2 = threading.Timer(60,toobou_limiter)
            t2.daemon = True
            t2.start()
            send_message(response)

    if messages.find('!song') != -1:
        if game == 'osu!':
            np_song = 'np.txt' #have osu!np output to folder bot.py is in
            if os.path.exists(np_song) == True:
                fo = open(np_song, 'r')
                song = fo.read()
                response = 'Currently playing: ' + song
                fo.close()
                send_message(response)
        else:
            np_song = 'current_song.txt'
            if os.path.exists(np_song) == True:
                fo = open(np_song, 'r')
                song = fo.read()
                if song != '':
                    response = 'Currently listening to: ' + song
                    fo.close()
                    send_message(response)
                else:
                    response = 'Not currently listening to anything.'
                    send_message(response)

    if messages.find('!bet ') != -1:
        sender_bet = messages.split('!bet ')[-1]
        if sender in already_bet and sender_bet == already_bet[sender]:
            response = 'You have already bet for that ' + sender + '.'
        elif sender in already_bet and sender_bet != already_bet[sender]:
            previous_bet = already_bet[sender]
            bets[previous_bet] = bets.get(previous_bet) - 1
            if bets[previous_bet] == 0:
                del bets[previous_bet]
            if sender_bet in bets:
                bets[sender_bet] = 1 ++ bets.get(sender_bet)
            else:
                bets[sender_bet] = 1
        else:
            if sender_bet in bets:
                bets[sender_bet] = 1 ++ bets.get(sender_bet)
            else:
                bets[sender_bet] = 1
            response = 'Thanks for thinking I will fail.'   
        already_bet[sender] = sender_bet
        send_message(response)
        print bets
        
    if messages.find('!bets') != -1:
        if bool(bets) == False:
            response = "No one thinks I'm going to throw this run away yet."
            send_message(response)
        else:
            winning_key = max(bets, key=bets.get)
            winning_value = bets[winning_key]
            winning_key = str(winning_key)
            winning_value = str(winning_value)
            response = winning_value + " people think I'm going to throw the run away at " + winning_key + '.'
            send_message(response)

    if messages.find('!resetbets') != -1 and sender == channel:
        bets = {}
        already_bet = {}

    if messages.find('!recheck') != -1 and sender == channel:
        channel_check(channel)

    if messages.find('!restart') != -1 and sender == channel:
        pass

    if messages.find('!exit') != -1 and sender == channel:
        irc.close()
        raw_input('Closing down.  Hit enter to conitnue.\n')
        loop = 2
        sys.exit()
    

#ideas to add: imgur album, osu skin 
#riot: masteries, runes, kda
#osu: rank, 
