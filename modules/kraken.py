#! /usr/bin/env python2.7

import modules.api_base as api

class Kraken(api.API):

    def __init__(self, base_url, default_headers, oauth_token = None, check_token = True):
        super(Kraken, self).__init__(base_url, default_headers)
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

    # Endpoints
    def root(self, headers = None, **kwargs):
        # Root gives information about your oauth key
        endpoint = "/"
        success, response = self.get(endpoint, headers, **kwargs)
        return success, response

    def get_stream(self, channel, headers = None, **kwargs):
        # Pass a channel that you would like the stream object for
        raise NotImplementedError

    def get_streams(self, channels, headers = None, **kwargs):
        # Pass an array of channel you would like to retrieve stream objects for
        raise NotImplementedError

