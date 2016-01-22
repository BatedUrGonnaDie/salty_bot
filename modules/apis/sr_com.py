#! /usr/bin/env python2.7

import modules.apis.api_base as api

class SRcomAPI(api.API):

    def __init__(self, session = None):
        super(SRcomAPI, self).__init__("http://www.speedrun.com/api/v1", session)

    # Embeds should be list of parameters
    def get_user_pbs(self, user, embeds = None, **kwargs):
        endpoint = "/users/{0}/personal-bests?embed={1}".format(user, self.join_embeds(embeds))
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_games(self, search_string, embeds = None, **kwargs):
        embeds = [] if None else embeds
        endpoint = "games?name={0}&embed={1}".format(search_string, self.join_embeds(embeds))
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_leaderboards(self, game, category, embeds = None, **kwargs):
        embeds = [] if None else embeds
        endpoint = "leaderboards/{0}/category/{1}?embed={2}".format(game, category, self.join_embeds(embeds))
        success, response = self.get(endpoint, **kwargs)
        return success, response

    # Easy function to join the embeds w/o needing to repeat in every function
    def join_embeds(self, embeds):
        return "" if embeds == None else ",".join(embeds)
