import requests    #required install module
import socket

#
import threading
import time
#decision librarys
import random

#Norms
import sys
import os

#File IO librarys
import xml.etree.ElementTree as ET

distro = "bomb_bot"
#code produced by bombmask

##this is the bot class
#create new bot with 
#<variablename> = bot()   :excellentgamer!excellentgamer@excellentgamer.tmi.twitch.tv PRIVMSG #happybythree :my familia is from Mxico
#:sander_bk!sander_bk@sander_bk.tmi.twitch.tv JOIN #happybythree
#:<user>!<useremail> </space> <type> <channel> :<data>
#PING :tmi.twitch.tv


class Bot:
    messagesSent = 0
    commandsSent = 0
    messagesRecv = 0
    welcomeMesgs = 0
    pingPongs = 0

    def __init__(self,data):#This is the first function that is called when you make a class object
        self.data = data
        self.PONG = 'PONG tmi.twitch.tv\r\n'
        self.irc = socket.socket()
        self.parse(self.data)
        self.limit = 0


    def run(self):
        self.connect()
        send = False

        while True:

            ircin = self.irc.recv(4096)
            self.messagesRecv += 1
            toformat = ircin.split('\r\n')[0] + '\r'
            print("Messages recived: {mr}\tMessages sent: {ms}\t\tCommands sent: {cs}\tWelcome messages: {wm}\r"\
                .format(mr = self.messagesRecv,ms=self.messagesSent,cs=self.commandsSent,wm=self.welcomeMesgs))
            if send and self.limit < 20:
                data = self.read(toformat)
                if data != self.PONG:


                    if data['message'] == ':!hello':
                        self.send("Hello {}!".format(data['user'][1:]))
                        self.commandsSent += 1
                    if data["message"] == ":!commands":
                        self.send("!hello and !info")
                        self.commandsSent += 1
                    if data["message"] == ":!info":
                        self.send("Hey Happy I got the bot working just for your stream, please don't break it :\ its not finished")
                        self.commandsSent += 1

                    if data['JL'] == 'JOIN':
                        self.welcomeMesgs += 1
                        self.send("Welcome to the stream {user}!!".format(user=data['user'][1:]))
                    
            elif not send:
                if 'HISTORYEND' in ircin:
                    send = True

            if not(self.limit < 15):
                time.sleep(20)



    def parse(self,fio,level=1):
        if level == 1:
            print("configuring")
            
            self.password = fio.find("OAUTH").text
            self.nick = fio.find("NICK").text
            self.channel = fio.find("./channel/name").text
            self.host = fio.find("./IRC/host").text
            self.port = int(fio.find("./IRC/port").text)
            
            #print("{}\t{}\t{}\t{}\t{}".format(self.password,self.nick,self.channel,self.host,self.port))


        if fio.getchildren():
            for child in fio:
                print("|{level}<element: {child}>".format(level='____'*(level-1),child=child.tag))
                if child.getchildren():
                    self.parse(child,level + 1)

        return 0

    def connect(self):
        irc = self.irc
        print "Connecting to channel: {channel}\nOn IRC server: {server}\nOn port: {port}\nWith Name: {name}\n\n"\
        .format(channel=self.channel,server=self.host,port=self.port,name=self.nick)

        irc.connect((self.host, self.port))
        irc.send('PASS ' + self.password + '\r\n')
        irc.send('NICK ' + self.nick + '\r\n')
        irc.send('JOIN ' + self.channel + '\r\n')

    def read(self,message):
        data = {}
        if 'PING :' in message:
            self.send(self.PONG)

            return self.PONG
        else:

            tmp = ''
            mode = 'user'
            types = ['user','mail','JL','channel','message']

            for i in types:
                data[i] = ''

            for l in message:
                if l == '\r':
                    return data
                if mode == 'user':
                    if l == '!':
                        mode = 'mail'

                    else:
                        data[mode] += l

                elif mode == 'mail':
                    if l == " ":
                        mode = "JL"
                    else:
                        data[mode] += l

                elif mode == 'JL':
                    if l == ' ':
                        mode = 'channel'
                    else:
                        data[mode] += l

                elif mode == 'channel':
                    if l == ' ':
                        mode = 'message'
                    else:
                        data[mode] += l

                elif mode == 'message':
                    if l == '\r':
                        break
                    data[mode] += l
                
            return data


    def send(self,send):
        if send == self.PONG:
            self.irc.send(send)
            self.pingPongs += 1
        else:
            to="PRIVMSG {channel} :{send}\r\n".format(channel=self.channel,send=send).encode("utf-8")
            self.messagesSent += 1
            self.irc.send(to)
            self.limit += 1

    def hello(self,data):
        pass
    def goodbye(self,data):
        pass
def bombmaskMain(**args):
    tree = ET.parse("bot_data.xml")
    root = tree.getroot()
    bots = root.find("bots")
    xGlob = root.find("botGlobals")
    config = root.find("builder")


    spawnedBots = []
    for i in bots:
        if i.attrib['on'] == 'y':
            spawnedBots.append(Bot(i))


    for i in spawnedBots:
        print(i.channel)

    botThr = []
    for i,n in zip(spawnedBots,range(len(spawnedBots))):
        botThr.append(threading.Thread(target=i.run))
        botThr[n].daemon = True
        botThr[n].start()
        print("spawned bot {}".format(i))

    time.sleep(5)
    while True:
        time.sleep(1)

     
if __name__ == "__main__":
    bombmaskMain()