#! /usr/bin/env python2.7

import modules.apis.api_base as api
from   modules.apis import api_errors

class YoutubeAPI(api.API):

    def __init__(self, key = None, session = None):
        if key == None:
            if session == None or not session.params["key"]:
                raise api_errors.AuthorizationRequiredError
            else:
                self.api_key = session.params["key"]
                del session.params["key"]
        else:
            self.api_key = key
        super(YoutubeAPI, self).__init__("https://www.googleapis.com/youtube/v3", session)

    def get_videos(self, ids, parts, tmp_key = None, **kwargs):
        # Ids and parts should be lists of the parameters
        key = tmp_key if tmp_key else self.api_key
        endpoint = "/videos?part={0}&id={1}&key={2}".format(
            ",".join(parts),
            ",".join(ids),
            key
        )
        success, response = self.get(endpoint, **kwargs)
        return success, response
