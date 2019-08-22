#! /usr/bin/env python3.7

import os

import modules.apis.api_base as api
from modules.apis import api_errors


class Kraken(api.API):

    def __init__(self, client_id=None, oauth=None, headers=None, cookies=None):
        if not client_id and not os.environ.get("SALTY_TWITCH_CLIENT_ID", None) and not oauth:
            raise api_errors.AuthorizationRequiredError
        super(Kraken, self).__init__("https://api.twitch.tv/kraken", headers=headers, cookies=cookies)
        self.oauth = oauth
        self.headers["Client-ID"] = client_id or os.environ["SALTY_TWITCH_CLIENT_ID"]
        self.headers["Accept"] = "application/vnd.twitchtv.v5+json"

    @property
    def oauth(self):
        return self._oauth

    @oauth.setter
    def oauth(self, oauth):
        self._oauth = oauth
        self.headers["Authorization"] = oauth

    # Endpoints
    def root(self, **kwargs):
        # Root gives information about your oauth key
        endpoint = "/"
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_stream(self, channel, **kwargs):
        # Pass a channel that you would like the stream object for
        endpoint = "/streams/{0}".format(channel)
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_streams(self, channels, **kwargs):
        # Pass an array of channel you would like to retrieve stream objects for
        endpoint = "/streams?channel={0}".format(','.join(channels))
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_steams_featured(self, **kwargs):
        endpoint = "/streams/featured"
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_streams_summarry(self, **kwargs):
        endpoint = "/streams/summary"
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_channel(self, channel, **kwargs):
        endpoint = "/channels/{0}".format(channel)
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_channel_authed(self, **kwargs):
        if not self.oauth:
            raise api_errors.AuthorizationRequiredError
        endpoint = "/channel"
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def put_channel(self, channel, data, **kwargs):
        if not self.oauth:
            raise api_errors.AuthorizationRequiredError
        endpoint = "/channels/{0}".format(channel)
        success, response = self.put(endpoint, data=data, **kwargs)
        return success, response
