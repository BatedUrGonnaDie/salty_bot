#! /usr/bin/env python2.7

import os

import modules.apis.api_base as api

class YoutubeAPI(api.API):

    def __init__(self, key = None, session = None):
        super(YoutubeAPI, self).__init__("https://www.googleapis.com/youtube/v3", session)
        # API key is required to use the youtube api
        self.api_key = key or os.environ["youtube_api_key"]

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
