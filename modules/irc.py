#! /usr/bin/env python2.7

import logging
import Queue
import socket
import ssl
import time
import threading

PASSTHROUGH_ACTIONS = (
    "PRIVMSG",
    "NOTICE",
    "USERSTATE",
    "GLOBALUSERSTATE",
    "HOSTTARGET",
    "CLEARCHAT",
    "JOIN",
    "PART",
    "MODE",
    "RECONNECT",
    "ROOMSTATE",
    "CAP",
)

class IRC(object):

    def __init__(self, host, port, username, oauth = "", use_ssl = False, callback = None):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.username = username
        self.oauth = oauth
        self.socket = None
        self.timeout_count = 0
        self.connected = False
        self.channels = set()
        self.capabilities = set()
        self.continue_loop = True
        self.create()
        self.callback = callback
        self.queue = Queue.Queue()
        self.worker_thread = threading.Thread(target=self.msg_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        self.tmp_threads = []

    def create(self):
        self.socket = socket.socket()
        self.socket.settimeout(600)
        if self.use_ssl:
            self.socket = ssl.wrap_socket(self.socket)

    def connect(self):
        self.socket.connect((self.host, self.port))
        for i in self.capabilities:
            self.capability(i)
        if self.oauth:
            self.raw("PASS {0}".format(self.oauth))
        self.raw("NICK {0}".format(self.username))
        time.sleep(.5)
        self.recv(4096)
        self.connected = True
        if self.channels:
            for i in self.channels:
                self.join(i)

    def disconnect(self):
        try:
            self.quit()
        except Exception:
            pass
        finally:
            self.socket.close()
            self.socket = None
            self.connected = False

    def reconnect(self):
        self.disconnect()
        self.create()
        self.connect()

    def raw(self, msg):
        self.socket.sendall("{0}\r\n".format(msg))

    def ping(self):
        self.raw("PING")

    def pong(self, host):
        self.raw("PONG {0}".format(host))

    def join(self, channel):
        self.raw("JOIN #{0}".format(channel))
        self.channels.add(channel)

    def part(self, channel):
        self.raw("PART #{0}".format(channel))
        self.channels.remove(channel)

    def quit(self):
        self.raw("QUIT")

    def capability(self, cap):
        self.raw("CAP REQ :{0}".format(cap))

    def privmsg(self, channel, msg):
        self.raw("PRIVMSG #{0} :{1}".format(channel, msg))

    def pm(self, user, msg):
        self.raw("PRIVMSG {0} :{1}".format(user, msg))

    def get_peer_ip(self):
        return self.socket.getpeername()[0]

    def recv(self, amount):
        inc_msg = self.socket.recv(amount)
        try:
            return inc_msg.decode("utf-8")
        except Exception, e:
            logging.exception(e)
            return inc_msg

    @staticmethod
    def tokenize(raw_msg):
        c_msg = {}
        msg_split = raw_msg.split(" ")
        if raw_msg.startswith(":"):
            msg_split.insert(0, "")
            c_msg["tags"] = {}
        elif msg_split[0]:
            c_msg["tags"] = IRC.process_tags(msg_split[0])
        if "!" in msg_split[1]:
            c_msg["sender"] = msg_split[1][1:].split("!")[0]
        else:
            c_msg["sender"] = msg_split[1][1:]
        c_msg["action"] = msg_split[2]
        try:
            c_msg["channel"] = msg_split[3]
        except IndexError:
            c_msg["channel"] = ""
        try:
            c_msg["message"] = " ".join(msg_split[4:])
            if c_msg["message"].startswith(":"):
                c_msg["message"] = c_msg["message"][1:]
        except IndexError:
            c_msg["message"] = ""
        return c_msg

    @staticmethod
    def process_tags(tags):
        tags_dict = dict(item.split("=") for item in tags[1:].split(";"))
        for k, v in tags_dict.iteritems():
            k.replace("\\:", ";")
            k.replace("\\s", " ")
            k.replace("\\\\", "\\")
            v.replace("\\:", ";")
            v.replace("\\s", " ")
            v.replace("\\\\", "\\")
        return tags_dict

    def msg_worker(self):
        while self.continue_loop:
            if self.queue.qsize > 20:
                t = threading.Thread(target=self.tmp_msg_worker)
                t.daemon = True
                t.start()
                self.tmp_threads.append(t)
            self.callback(self.queue.get())
            self.queue.task_done()
            if self.tmp_threads and self.queue.empty():
                for i in self.tmp_threads:
                    i.join()

    def tmp_msg_worker(self):
        while True:
            try:
                self.callback(self.queue.get(False))
                self.queue.task_done()
            except Queue.Empty:
                break
        return

    def main_loop(self):
        self.socket.settimeout(10)
        msg_buffer = ""
        lines = []
        while self.continue_loop:
            try:
                msg_buffer += self.recv(4096)
            except socket.timeout:
                if self.timeout_count < 60:
                    self.timeout_count += 1
                    continue
                else:
                    self.reconnect()
                    continue
            if msg_buffer == "":
                self.reconnect()
                continue
            lines += msg_buffer.split("\r\n")
            while len(lines) > 1:
                current_message = lines.pop(0)
                if current_message == "":
                    continue
                if current_message.startswith("PING"):
                    self.pong(current_message.split("PING ")[0])
                    continue

                try:
                    msg_parts = self.tokenize(current_message)
                except Exception, e:
                    logging.error(current_message)
                    logging.exception(e)
                    continue
                msg_parts["bot_name"] = self.username
                msg_parts["original"] = current_message

                if msg_parts["action"] == "PRIVMSG":
                    try:
                        print "{0} {1}: {2}".format(msg_parts["channel"], msg_parts["sender"], msg_parts["message"])
                    except Exception:
                        pass
                if msg_parts["action"] == "CAP":
                    if msg_parts["message"].split(" ")[0] == "ACK":
                        self.capabilities.add(msg_parts["message"].split(" ", 1)[1])
                    else:
                        self.capabilities.remove(msg_parts["message"].split(" ", 1)[1])

                if self.callback and msg_parts["action"] in PASSTHROUGH_ACTIONS:
                    self.queue.put(msg_parts)
            if lines[0] != "":
                msg_buffer = lines[0]
            else:
                msg_buffer = lines.pop(0)
