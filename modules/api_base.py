#! /usr/bin/env python2.7

import requests

class API(object):
    # This class should be inherited by more unique API specific classes
    # See kraken.py for an example

    def __init__(self, base_url, default_headers):
        self.base_url = base_url
        self.headers = default_headers

    # Define all HTTP verb calls
    # Each return the status of the call (True/False), and the return payload
    def get(self, endpoint, headers = None, **kwargs):
        if headers:
            # Update the base headers with any new headers
            # But w/o changing the base ones
            headers = self.update_headers(headers)
        url = self.base_url + endpoint

        try:
            data = requests.get(url=url, headers=headers, **kwargs)
            data.raise_for_status()
            data_decode = data.json()
            return True, data_decode
        except requests.exceptions.HTTPError:
            return False, data

    def post(self, endpoint, data, headers = None, **kwargs):
        if headers:
            headers = self.update_headers(headers)
        url = self.base_url + endpoint

        try:
            data = requests.post(url=url, headers=headers, data=data, **kwargs)
            data.raise_for_status()
            data_decode = data.json()
            return True, data_decode
        except requests.exceptions.HTTPError:
            return False, data

    def put(self, endpoint, data, headers = None, **kwargs):
        if headers:
            headers = self.update_headers(headers)
        url = self.base_url + endpoint

        try:
            data = requests.put(url=url, headers=headers, data=data, **kwargs)
            data.raise_for_status()
            data_decode = data.json()
            return True, data_decode
        except requests.exceptions.HTTPError:
            return False, data

    # Woker functions
    def update_headers(self, headers):
        tmp = self.headers.copy()
        return tmp.update(headers)
