import requests    #required install module
import socket

#
import threading

#decision librarys
import random

#Norms
import sys
import os

#File IO librarys
import xml.etree.ElementTree as ET



##this is the bot class
#create new bot with 
#<variablename> = bot()

class Bot:
    def __init__(self,bot_config_number=-1):#This is the first function that is called when you make a class object
        
        if bot_config_number == -1:
            return 
            
        spawnID = self.readConfig(bot_config_number)
        self.spawn(spawnID)
        self.start()

    def spawn(self):#create starting variables
        pass

    def start(self):#startup script
        pass

    def bot_info_file_io(self):#read file datas
        pass

    def connect_to_irc(self):#connect to IRC with PASS AUTH and NICK
        pass

    def send_to_irc(self,data):#send data to out stream
        pass

    def exec_command(self,command):#Figure out command from IRC chat
        pass


    def parser(self):
        tree = ET.parse("bot_data.xml")
        


class Botcare:
    def __init__(self):
        pass
        
    def file_setup(self):
        if not os.path.exists("bot_data.xml"):
            tree = ET.ElementTree
            root = ET.Element("salty")
            tree._setroot(root)

class BotLoader:
    def __init__():
        pass


#class botHandler:



if __name__ == "__main__":
    pass


def bombmaskMain(args):
    pass

