#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-

import socket

class UpdateListenr:

    def __init__(self, listen_port):
        self.web_secret = ""
        self.port = listen_port
        host = socket.gethostbyname(socket.gethostname())
        self.s = socket.socket(())
        self.s.bind((host, 6666))

    def main_listen(self):
        self.s.listen(1)
        connection, address = self.s.accept()
        secret = self.s.recv(1024)
        if secret != self.web_secret:
            connection.close()
            raise ValueError
        else:
            to_update = self.s.recv(4096)
            connection.close()
            return to_update
