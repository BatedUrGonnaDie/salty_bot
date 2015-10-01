#! /usr/bin/env python2.7

import modules.apis.api_base as api

class NewbsAPI(api.API):

    def __init__(self, default_headers = None):
        if not default_headers:
            default_headers = {}
        super(NewbsAPI, self).__init__("https://leagueofnewbs.com/api", default_headers)

    def get_song(self, channel, **kwargs):
        endpoint = "/users/{}/songs".format(channel)
        success, response = self.get(endpoint, **kwargs)
        return success, response
