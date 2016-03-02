#! /usr/bin/env python2.7

import modules.apis.api_base as api
from   modules.apis import api_errors

class OsuAPI(api.API):

    def __init__(self, key = None, session = None):
        if key == None:
            if session == None or not session.params["k"]:
                raise api_errors.AuthorizationRequiredError
            else:
                self.api_key = session.params["k"]
                del session.params["k"]
        else:
            self.api_key = key
        super(OsuAPI, self).__init__("https://osu.ppy.sh/api", session)

    def get_user(self, user, tmp_key = None, **kwargs):
        key = tmp_key if tmp_key else self.api_key
        endpoint = "/get_user?k={}&user={}".format(key, user)
        success, response = self.get(endpoint, **kwargs)
        return success, response

    def get_beatmap(self, map_id, tmp_key = None, **kwargs):
        # Map_id is b={id} or s={id}, include the type in your argument
        key = tmp_key if tmp_key else self.api_key
        endpoint = "/get_beatmaps?k={}&{}".format(key, map_id)
        success, response = self.get(endpoint, **kwargs)
        return success, response
