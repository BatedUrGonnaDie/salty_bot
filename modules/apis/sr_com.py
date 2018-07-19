#! /usr/bin/env python3.7

import modules.apis.api_base as api


class SRcomAPI(api.API):

    def __init__(self, headers=None, cookies=None):
        super(SRcomAPI, self).__init__("http://www.speedrun.com/api/v1", headers=headers, cookies=cookies)

    # Embeds should be list of parameters
    def get_user_pbs(self, user, embeds=None, **kwargs):
        endpoint = "/users/{0}/personal-bests?embed={1}".format(user, self.join_embeds(embeds))
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_game(self, game_abbrev, embeds=None, **kwargs):
        embeds = [] if None else embeds
        endpoint = "/games/{0}?embed={1}".format(game_abbrev, self.join_embeds(embeds))
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_games(self, query_params, embeds=None, **kwargs):
        embeds = [] if None else embeds
        endpoint = "/games?embed={0}".format(self.join_embeds(embeds))
        success, response = self.get(endpoint, params=query_params, **kwargs)
        return success, response

    def get_leaderboards(self, game, category, embeds=None, **kwargs):
        embeds = [] if None else embeds
        endpoint = "/leaderboards/{0}/category/{1}?embed={2}".format(game, category, self.join_embeds(embeds))
        success, response = self.get(endpoint, **kwargs)
        return success, response

    # Easy function to join the embeds w/o needing to repeat in every function
    def join_embeds(self, embeds):
        return "" if embeds is None else ",".join(embeds)
