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



##this is the bot class
#create new bot with 
#<variablename> = bot()   :excellentgamer!excellentgamer@excellentgamer.tmi.twitch.tv PRIVMSG #happybythree :my familia is from Mxico
#:sander_bk!sander_bk@sander_bk.tmi.twitch.tv JOIN #happybythree
#:<user>!<useremail> </space> <type> <channel> :<data>
#

class Bot:
    def __init__(self,data):#This is the first function that is called when you make a class object
        self.data = data
        self.irc = socket.socket()
        self.parse(self.data)
        self.connect()



    def run(self):
        while True:

            k = self.irc.recv(4096)
            print(k) 

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
                print("|{level}{child}".format(level='____'*(level-1),child=child))
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

    def send(self,send):
        to="PRIVMSG {channel} :{send}\r\n".format(channel=self.channel,send=send).encode("utf-8")
        print(to)
        self.irc.send(to)

    def compile(self,string,**args):
        pass



        
if __name__ == "__main__":
    bombmaskMain()

def bombmaskMain(args):
    tree = ET.parse("bot_data.xml")
    root = tree.getroot()
    bots = root.find("bots")
    xGlob = root.find("botGlobals")
    config = root.find("builder")

    spawnedBots = []
    for i in bots:
        spawnedBots.append(Bot(i))

    for i in spawnedBots:
        print(i.channel)

