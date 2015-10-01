#! /usr/bin/env python2.7

import modules.apis.api_base as api
import modules.apis.kraken_errors as kraken_errors

class Kraken(api.API):

    def __init__(self, oauth_token = None, default_headers = None, check_token = True):
        if not default_headers:
            default_headers = {}
        super(Kraken, self).__init__("https://api.twitch.tv/kraken", default_headers)
        self.oauth_token = oauth_token
        if self.oauth_token and check_token:
            self.check_token()
        # Feel free to set these manually, they are just here for convenience
        self.user = ""
        self.scopes = []

    def set_oauth(self, oauth_token, check_token = True):
        self.oauth_otken = oauth_token
        if check_token:
            self.check_token()

    # Get scopes and who the token is valid for
    def check_token(self):
        header = {"Authorization": "Oauth " + self.oauth_token}
        success, response = self.root(header)
        if success and response["token"]["valid"]:
            self.user = response["token"]["user_name"]
            self.scopes = response["token"]["authorization"]["scopes"]
            return True
        return False

    def find_token(self, oauth, headers):
        if headers["Authorization"]: return headers["Authorization"]
        if oauth: return oauth
        if self.oauth_token: return self.oauth_token
        raise kraken_errors.AuthorizationRequiredError("This endopint requires an oauth toekn.")

    # Endpoints
    def root(self, headers = None, **kwargs):
        # Root gives information about your oauth key
        endpoint = "/"
        success, response = self.get(endpoint, headers=headers, **kwargs)
        return success, response

    def get_stream(self, channel, headers = None, **kwargs):
        # Pass a channel that you would like the stream object for
        endpoint = "/streams/{0}".format(channel)
        success, response = self.get(endpoint, headers=headers, **kwargs)
        return success, response

    def get_streams(self, channels, headers = None, **kwargs):
        # Pass an array of channel you would like to retrieve stream objects for
        endpoint = "/streams?channel={0}".format(','.join(channels))
        success, response = self.get(endpoint, headers=headers, **kwargs)
        return success, response

    def get_steams_featured(self, headers = None, **kwargs):
        endpoint = "/streams/featured"
        success, response = self.get(endpoint, headers=headers, **kwargs)
        return success, response

    def get_streams_summarry(self, headers = None, **kwargs):
        endpoint = "/streams/summary"
        success, response = self.get(endpoint, headers=headers, **kwargs)
        return success, response

    def get_channel(self, channel, headers = None, **kwargs):
        endpoint = "/channels/{0}".format(channel)
        success, response = self.get(endpoint, headers=headers, **kwargs)
        return success, response

    def get_channel_authed(self, oauth = None, headers = None, **kwargs):
        headers["Authorization"] = self.find_token(oauth, headers)
        endpoint = "/channel"
        success, response = self.get(endpoint, headers=headers, **kwargs)
        return success, response

    def put_channel(self, channel, data, oauth = None, headers = None, **kwargs):
        headers["Authorization"] = self.find_token(oauth, headers)
        endpoint = "/channels/{0}".format(channel)
        success, response = self.put(endpoint, headers=headers, data=data, **kwargs)
        return success, response

