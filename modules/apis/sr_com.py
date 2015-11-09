#! /usr/bin/env python2.7

import modules.apis.api_base as api

class SRcomAPI(api.API):

    def __init__(self, session = None):
        super(SRcomAPI, self).__init__("http://www.speedrun.com/api/v1", session)

    def get_user_pbs(self, user, embeds = "", **kwargs):
        # Embeds should be list of parameters
        endpoint = "/users/{0}/personal-bests?embed={1}".format(user, ",".join(embeds))
        success, response = self.get(endpoint, **kwargs)
        return success, response
