#! /usr/bin/env python3.7

import os

import modules.apis.api_base as api
from modules.apis import api_errors


class OsuAPI(api.API):

    def __init__(self, key=None, headers=None, cookies=None):
        self.api_key = key or os.environ.get("OSU_API_KEY", None)
        if not self.api_key:
            raise api_errors.AuthorizationRequiredError
        super(OsuAPI, self).__init__("https://osu.ppy.sh/api", headers=headers, cookies=cookies)

    def get_user(self, user, tmp_key=None, **kwargs):
        key = tmp_key if tmp_key else self.api_key
        endpoint = "/get_user?k={}&u={}".format(key, user)
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_beatmap(self, map_id, tmp_key=None, **kwargs):
        # Map_id is s={id}&b={id} s is set id and b is beatmap id
        key = tmp_key if tmp_key else self.api_key
        endpoint = "/get_beatmaps?k={}&{}".format(key, map_id)
        success, response = self.get(endpoint, **kwargs)
        return success, response
