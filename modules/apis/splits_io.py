#! /usr/bin/env python3.7

import modules.apis.api_base as api


class SplitsIOAPI(api.API):

    def __init__(self, headers=None, cookies=None):
        super(SplitsIOAPI, self).__init__("https://splits.io/api/v3", headers=headers, cookies=cookies)

    def get_user_pbs(self, user, **kwargs):
        endpoint = "/users/{0}/pbs".format(user)
        success, response = self.get(endpoint, **kwargs)
        return success, response
