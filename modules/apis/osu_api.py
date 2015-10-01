#! /usr/bin/env python2.7

import os

import modules.apis.api_base as api

class OsuAPI(api.API):

    def __init__(self, key = None, default_headers = None):
        if not default_headers:
            default_headers = {}
        super(OsuAPI, self).__init__("https://osu.ppy.sh/api", default_headers)
        # API key is required to use the osu api
        self.api_key = key or os.environ["osu_api_key"]

    def get_user(self, user, tmp_key = None, **kwargs):
        key = tmp_key if tmp_key else self.api_key
        endpoint = "/get_user?k={}&user={}".format(key, user)
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_beatmap(self, map_id, tmp_key = None, **kwargs):
        key = tmp_key if tmp_key else self.api_key
        endpoint = "/get_beatmaps?k={}&{}".format(key, map_id)
        success, response = self.get(endpoint, **kwargs)
        return success, response