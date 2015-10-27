#! /usr/bin/env python2.7

import modules.apis.api_base as api

class SRLAPI(api.API):

    def __init__(self, session = None):
        super(SRLAPI, self).__init__("http://api.speedrunslive.com", session)

    def get_races(self, **kwargs):
        endpoint = "/races"
        success, response = self.get(endpoint, **kwargs)
        return success, response
