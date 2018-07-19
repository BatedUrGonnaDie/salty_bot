#! /usr/bin/env python3.7

import logging

import requests


class API(object):
    # This class should be inherited by more unique API specific classes
    # See kraken.py for an example
    def __init__(self, base_url, headers=None, cookies=None):
        self.base_url = base_url
        # These headers and cookies will be sent with every request
        self.headers = headers if headers else {}
        self.cookies = cookies if cookies else {}

    # Define all HTTP verb calls
    # Each return the status of the call (True/False), and the return payload
    # ALl returns will be decoded JSON if success is True, otherwise the
    # return data is not decoded incase the server doesn't send back valid JSON
    def get(self, endpoint, params=None, **kwargs):
        url = self.base_url + endpoint

        try:
            data = requests.get(url=url, params=params, headers=self.headers, cookies=self.cookies, **kwargs)
            data.raise_for_status()
            data_decode = data.json()
            return True, data_decode
        except requests.exceptions.HTTPError:
            return False, data
        except Exception as e:
            logging.exception(e)
            return None, "Uncaught exception from requests."

    def post(self, endpoint, data, **kwargs):
        url = self.base_url + endpoint

        try:
            data = requests.post(url=url, headers=self.headers, cookies=self.cookies, data=data, **kwargs)
            data.raise_for_status()
            data_decode = data.json()
            return True, data_decode
        except requests.exceptions.HTTPError:
            return False, data
        except Exception as e:
            logging.exception(e)
            return None, "Uncaught exception from requests."

    def put(self, endpoint, data, **kwargs):
        url = self.base_url + endpoint

        try:
            data = requests.put(url=url, headers=self.headers, cookies=self.cookies, data=data, **kwargs)
            data.raise_for_status()
            data_decode = data.json()
            return True, data_decode
        except requests.exceptions.HTTPError:
            return False, data
        except Exception as e:
            logging.exception(e)
            return None, "Uncaught exception from requests."

    def delete(self, endpoint, **kwargs):
        url = self.base_url + endpoint

        try:
            data = requests.delete(url=url, headers=self.headers, cookies=self.cookies, **kwargs)
            data.raise_for_status()
            data_decode = data.json()
            return True, data_decode
        except requests.exceptions.HTTPError:
            return False, data
        except Exception as e:
            logging.exception(e)
            return None, "Uncaught exception from requests."
