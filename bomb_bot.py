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
    pingPongs= 0

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


                    if data['message'] == ':!hello' and data["user"] == ":bomb_mask":
                        self.send("Hello {}!".format(data['user'][1:]))
                        self.commandsSent += 1

                    if ":!spam" in data["message"] and data["user"] == ":bomb_mask":
                        for i in range(10):
                            self.send("{message} -{user} {count}/9".format(message=data["message"][6:],user=data["user"][1:],count=i))
                            time.sleep(1.4)

                    if data["message"] == ":!checkBan":
                        self.send("*Am I banned :(*")
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
        print("Connecting to channel: {channel}\nOn IRC server: {server}\nOn port: {port}\nWith Name: {name}\n\n"\
        .format(channel=self.channel,server=self.host,port=self.port,name=self.nick))

        irc.connect((self.host, self.port))
        irc.send('PASS ' + self.password + '\r\n')
        irc.send('NICK ' + self.nick + '\r\n')
        irc.send('JOIN ' + self.channel + '\r\n')

    def read(self,message):
        data = {} #Python dictionary
        if 'PING :' in message: #if there is a PING message then we don't parse the string
            self.send(self.PONG)
 
            return self.PONG #end the function and return our data
        else:
 
            tmp = ''  #Umm I don't know why this is here, I stopped using it
            mode = 'user' #My parser uses a weird mode-ing system, I think there is a better way to do this then a 'mode'
            types = ['user','mail','JL','channel','message'] #the parts I am parseing for JL is the join leave privmesg
 
            for i in types: #this loop populates the dictionary
                data[i] = '' #populate with empty strings
 
            for l in message:
                if l == '\r': #if it looks like we are at the end of the string end the loop and return the data(which is a dictionary)
                    return data
               
                #the format is
                #if we are in mode'Mode'
                        #check if we are at the end of the string (you know like how the message has different things that show what data is what (like the message comes after the  ':'))
                        #else add the current character to the dict string
 
                if mode == 'user':#looking for the data that is the user part of the string
                    if l == '!':#Signal that we found all of the data that we are calling user
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


def bombmaskMain(**args):
    #This section is just setup for reading an xml file
    tree = ET.parse("bot_data.xml") #THis opens the file with the xml parser
    root = tree.getroot()           #THis opens the data of the file, XML stuff
    bots = root.find("bots")        #this finds the xml tag 'bots' and stores that tag in the var bots
    xGlob = root.find("botGlobals") #THis finds the xml tag botGlobals. Ill use this later for when I have data I need to share with other bots
    config = root.find("builder")   #Also Unused so far, this will provide information about what the bot should do


    spawnedBots = [] #array(I guess its called a list really) so that I can keep track of bots, this helps because I don't know how many bots I will have when it runs
    #so I need to make sure that it can be modular

    for i in bots:#this opens the tags in the bots tags, IE bot>bot1, then bot>bot2 and it will loop over all the bot configs
        if i.attrib['on'] == 'y':#check if the bot is set to turn on
            spawnedBots.append(Bot(i))#create bot and add it to the list if we want to use it. it takes 'i' like a config


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
