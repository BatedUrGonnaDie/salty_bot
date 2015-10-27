#! /usr/bin/env python2.7

import modules.apis.api_base as api

class NewbsAPI(api.API):

    def __init__(self, session = None):

        super(NewbsAPI, self).__init__("https://leagueofnewbs.com/api", session)

    def get_song(self, channel, **kwargs):
        endpoint = "/users/{}/songs".format(channel)
        success, response = self.get(endpoint, **kwargs)
        return success, response
