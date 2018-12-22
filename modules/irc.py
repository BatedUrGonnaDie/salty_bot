#! /usr/bin/env python3.7

import logging
import queue
import socket
import ssl
import threading
import time
from typing import Any, Dict, List, Set

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
    "USERNOTICE"
)


class IRC:

    def __init__(self,
                 host: str,
                 port: int,
                 username: str,
                 oauth="",
                 use_ssl=False,
                 callback=None,
                 max_worker_threads=5) -> None:
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.username = username
        self.oauth = oauth
        self.socket = socket.socket()
        self.connected = False
        self.channels: Set[str] = set()
        self.capabilities: Set[str] = set()
        self.continue_loop = True
        self.create()
        self.callback = callback
        self.msg_queue: queue.Queue = queue.Queue()
        self.msg_queue_size = 0
        self.logger = logging.getLogger("IRC.IRC")

        self.worker_thread = threading.Thread(target=self.msg_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        if max_worker_threads < 0:
            max_worker_threads = 0
        self.max_worker_threads = max_worker_threads
        self.tmp_threads = 0

    def create(self) -> None:
        self.socket = socket.socket()
        self.socket.settimeout(600)
        if self.use_ssl:
            self.socket = ssl.wrap_socket(self.socket)

    def connect(self) -> None:
        sleep_time = 2
        while True:
            try:
                self.socket.connect((self.host, self.port))
            except ValueError as e:
                self.logger.error("Tried to connect to already connected socket!")
                self.disconnect()
                self.create()
                continue
            except Exception as e:
                self.logger.exception(e)
                time.sleep(sleep_time)
                sleep_time = sleep_time ** 2
                continue
            self.capability(" ".join(self.capabilities))
            if self.oauth:
                self.raw("PASS {0}".format(self.oauth))
            self.raw("NICK {0}".format(self.username))
            time.sleep(.5)
            self.connected = True
            if self.channels:
                for i in self.channels:
                    self.join(i)
                    time.sleep(.2)
            break

    def disconnect(self) -> None:
        try:
            self.quit()
        except Exception:
            pass
        finally:
            self.socket.close()
            self.connected = False

    def reconnect(self) -> None:
        self.disconnect()
        self.create()
        self.connect()

    def raw(self, msg) -> None:
        self.socket.sendall("{0}\r\n".format(msg).encode("utf-8"))

    def ping(self) -> None:
        self.raw("PING")

    def pong(self, host: str) -> None:
        self.raw("PONG {0}".format(host))

    def join(self, channel: str) -> None:
        self.raw("JOIN #{0}".format(channel))
        self.channels.add(channel)

    def part(self, channel: str) -> None:
        self.raw("PART #{0}".format(channel))
        self.channels.remove(channel)

    def quit(self) -> None:
        self.raw("QUIT")

    def capability(self, cap: str) -> None:
        self.raw("CAP REQ :{0}".format(cap))

    def privmsg(self, channel: str, msg: str) -> None:
        self.raw("PRIVMSG #{0} :{1}".format(channel, msg))

    def pm(self, user: str, msg: str) -> None:
        self.raw("PRIVMSG {0} :{1}".format(user, msg))

    def get_peer_ip(self) -> None:
        return self.socket.getpeername()[0]

    def recv(self, amount: int) -> str:
        inc_msg = self.socket.recv(amount)
        return inc_msg.decode("utf-8")

    @staticmethod
    def parse(msg: str) -> Dict[str, Any]:
        position = 0
        next_space = 0
        c_msg: Dict[str, Any] = {
            "raw": msg,
            "tags": {},
            "prefix": None,
            "action": None,
            "params": []
        }
        msg = msg.strip("\r\n")
        if msg[position] == "@":
            next_space = msg.find(" ")
            c_msg["tags"] = IRC.process_tags(msg[:next_space])
            position = next_space + 1

        while msg[position] == " ":
            position += 1

        if msg[position] == ":":
            next_space = msg.find(" ", position)
            c_msg["prefix"] = msg[position: next_space]
            position = next_space + 1

            while position == " ":
                position += 1

        next_space = msg.find(" ", position)

        if next_space == -1:
            if len(msg) > position:
                c_msg["action"] = msg[position:]
            return c_msg

        c_msg["action"] = msg[position: next_space]
        position = next_space + 1

        while msg[position] == " ":
            position += 1

        while position < len(msg):
            next_space = msg.find(" ", position)

            if msg[position] == ":":
                c_msg["params"].append(msg[position + 1:])
                break

            if next_space != -1:
                c_msg["params"].append(msg[position: next_space])
                position = next_space + 1

                while msg[position] == " ":
                    position += 1

                continue

            if next_space == -1:
                c_msg["params"].append(msg[position:])
                break

        return c_msg

    @staticmethod
    def process_tags(tags: str) -> Dict[str, str]:
        tags_dict: Dict[str, str] = {}
        for item in tags[1:].split(";"):
            tmp = item.split("=")
            tags_dict[tmp[0]] = tmp[1]
        escaped_dict = {}
        for k, v in tags_dict.items():
            new_k = k.replace("\\:", ";").replace("\\s", " ").replace("\\\\", "\\")
            new_v = v.replace("\\:", ";").replace("\\s", " ").replace("\\\\", "\\")
            escaped_dict[new_k] = new_v
        return escaped_dict

    def msg_worker(self) -> None:
        while self.continue_loop:
            if self.msg_queue_size > 5 and self.max_worker_threads < self.tmp_threads:
                self.logger.info("Spawning worker thread.")
                t = threading.Thread(target=self.tmp_msg_worker)
                t.daemon = True
                t.start()
                self.tmp_threads += 1
            try:
                self.callback(self.msg_queue.get())
            except Exception as e:
                self.logger.exception(e)
            self.msg_queue_size -= 1
            self.msg_queue.task_done()

    @staticmethod
    def extra_parse(msg: str) -> Dict[str, Any]:
        c_msg = IRC.parse(msg)
        if c_msg["action"] in ("PRIVMSG", "NOTICE", "HOSTTARGET"):
            c_msg["message"] = c_msg["params"][1]
            c_msg["sender"] = c_msg["prefix"].split("!")[0][1:]
        if c_msg["action"] in ("ROOMSTATE", "USERSTATE", "JOIN", "PRIVMSG", "NOTICE", "HOSTTARGET", "CLEARCHAT", "USERNOTICE", "JOIN", "PART", "MODE"):
            c_msg["channel"] = c_msg["params"][0]
        return c_msg

    def tmp_msg_worker(self) -> None:
        while True:
            try:
                self.callback(self.msg_queue.get(False))
                self.msg_queue_size -= 1
                self.msg_queue.task_done()
            except queue.Empty:
                break
        self.tmp_threads -= 1
        return

    def main_loop(self) -> None:
        msg_buffer = ""
        lines: List[str] = []
        while self.continue_loop:
            try:
                tmp_buffer = self.recv(4096)
            except socket.timeout as e:
                if self.continue_loop:
                    self.reconnect()
                continue

            self.timeout_count = 0

            if tmp_buffer == "":
                if self.continue_loop:
                    self.logger.info("Connection for {0} reset, reconnecting.".format(self.username))
                    self.reconnect()
                continue
            msg_buffer += tmp_buffer
            lines += msg_buffer.split("\r\n")
            while len(lines) > 1:
                current_message = lines.pop(0)
                if current_message == "":
                    continue
                msg_parts = self.extra_parse(current_message)
                if msg_parts["action"] == "PING":
                    self.pong(msg_parts["params"][0])
                    continue

                msg_parts["bot_name"] = self.username

                if msg_parts["action"] == "CAP":
                    if msg_parts["params"][1] == "ACK":
                        for i in msg_parts["params"][2].split(" "):
                            self.capabilities.add(i)
                    elif msg_parts["params"][1] == "NAK":
                        for i in msg_parts["params"][2].split(" "):
                            if i in self.capabilities:
                                self.capabilities.remove(i)

                if self.callback:
                    if msg_parts["action"] in PASSTHROUGH_ACTIONS:
                        self.msg_queue.put(msg_parts)
                        self.msg_queue_size += 1
                else:
                    raise ValueError("Callback should be defined before calling main_loop.")
            if lines[0] != "":
                msg_buffer = lines[0]
            else:
                msg_buffer = lines.pop(0)
