F#! /usr/bin/python2.7
# -*- coding: utf8 -*-

import requests    #required install module
import socket
import threading
import Queue
import random
import time
import sys
import os
from var import *
from configure import *

#Functions
def file_check(name):
    file_name = name + '.txt'
    if os.path.exists(file_name) != True:
        fo = open(file_name, 'w')
        fo.close()
        print file_name + ' created.'

def boolify(api):
    if api == 'y':
        return True
    elif api == 'n':
        return False
    
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
            try:
                game = data_stream['game'].lower()
            except AttributeError:
                game = data_stream['game']
            global title
            try:
                title = data_channel['status'].lower()
            except AttributeError:
                title = data_channel['status']
            print str(channel) + '\n' + str(game) + '\n' + str(title)
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
        salty_says = nick + ': ' + response
        salty_says = salty_says.encode('utf-8')
        print salty_says
    else:
        print 'Sending to quckly'

def send_after_number_time():
    global messages_received
    if messages_received > message_after_number:
        send_message(automated_message)
        messages_reveived = 0
    t3 = threading.Timer(message_number_timer,send_after_number_time)
    t3.daemon = True
    t3.start()

def quote_retrieve():
    file_name = 'quotes'
    file_check(file_name)
    quote_lines = sum(1 for line in open('quotes.txt', 'r'))
    if quote_lines == 0:
        quote = 'No quotes added.'
    elif quote_lines == 1:
        quote = open('quotes.txt', 'r').readline()
    else:
        select_quote = random.randrange(1, quote_lines, 1)
        quote = open('quotes.txt', 'r').readlines()
        quote = quote[select_quote]
    return quote

def pun_retrieve():
    file_name = 'puns'
    file_check(file_name)
    pun_lines = sum(1 for line in open('puns.txt', 'r'))
    if pun_lines == 0:
        pun = 'No puns added.'
    elif pun_lines == 1:
        pun = open('puns.txt', 'r').readline()
    else:
        select_pun = random.randrange(1, pun_lines, 1)
        pun = open('puns.txt', 'r').readlines()
        pun = pun[select_pun]
    return pun



#Main Program
nick, password, message_after_number, message_number_timer, automated_message = configure()

channel = raw_input('Enter Channel to Join: ')

irc = socket.socket()
host = 'irc.twitch.tv'
port = 6667

limiter()

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
    os.remove('config.ini')
    irc.close()
    print 'Login was un successful, deleting config file, please try again.'
    raw_input('Hit enter to close this program.\n')
    destroy_loop = 1


#send_after_time()
send_after_number_time()
while loop == 1 and not destroy_loop:

    messages = irc.recv(4096)
    messages = messages.split('\r\n')[0]
    messages = messages.lower()
    try:
        action = messages.split(' ')[1]
    except:
        action = ''
    if action == 'privmsg':
        sender = messages.split(":")[1].split("!")[0]
        message_body = ":".join(messages.split(":")[2:])
        print sender + ': ' + message_body
        messages_received += 1
    if action == 'mode':
        if '+o ' in messages:
            admin_extract = messages.split('+o ')[-1]
            fo = open('admins.txt', 'a+')
            admin_file = fo.read()
            fo.close()
            if admin_extract in admin_file:
                pass
            else:
                print admin_extract + ' added to admins.txt.'
                fo = open('admins.txt', 'a+')
                fo.write(admin_extract)
                fo.close()
    if action == 'join':
        sender = messages.split(":")[1].split("!")[0]
        print sender + ' has joined the room!'
    if action == 'part':
        sender = messages.split(":")[1].split("!")[0]
        print sender + ' has left the room.'

    if messages.startswith('ping'):
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
            quote = quote_retrieve()
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
            pun = pun_retrieve()
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
            response = "No one has bet yet."
            send_message(response)
        else:
            winning_key = max(bets, key=bets.get)
            winning_value = bets[winning_key]
            winning_key = str(winning_key)
            winning_value = str(winning_value)
            response = winning_value + " people have bet on  " + winning_key + '.'
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


#ideas to add: pb, imgur album, osu skin
#riot: masteries, runes, kda
#osu: rank
