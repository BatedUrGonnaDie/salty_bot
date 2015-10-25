#! /usr/bin/env python2.7

import modules.apis.api_base as api

class SRLAPI(api.API):

    def __init__(self, default_headers = None):
        if not default_headers:
            default_headers = {}
        super(SRLAPI, self).__init__("http://api.speedrunslive.com", default_headers)

    def get_races(self, **kwargs):
        endpoint = "/races"
        success, response = self.get(endpoint, **kwargs)
        return success, response
