#! /usr/bin/env python2.7

import requests

class API(object):
    # This class should be inherited by more unique API specific classes
    # See kraken.py for an example

    def __init__(self, base_url, session = None):
        self.base_url = base_url
        if session == None:
            self.session = requests.Session()
        else:
            self.session = session

    # Define all HTTP verb calls
    # Each return the status of the call (True/False), and the return payload
    def get(self, endpoint, **kwargs):
        url = self.base_url + endpoint

        try:
            data = self.session.get(url=url, **kwargs)
            data.raise_for_status()
            data_decode = data.json()
            return True, data_decode
        except requests.exceptions.HTTPError:
            return False, data

    def post(self, endpoint, data, **kwargs):
        url = self.base_url + endpoint

        try:
            data = self.session.post(url=url, data=data, **kwargs)
            data.raise_for_status()
            data_decode = data.json()
            return True, data_decode
        except requests.exceptions.HTTPError:
            return False, data

    def put(self, endpoint, data, **kwargs):
        url = self.base_url + endpoint

        try:
            data = self.session.put(url=url, data=data, **kwargs)
            data.raise_for_status()
            data_decode = data.json()
            return True, data_decode
        except requests.exceptions.HTTPError:
            return False, data
