#! /usr/bin/env python3.7

import logging
import os

from twitchAPI.twitch import Twitch
from twitchAPI.types import TwitchAPIException

from modules.apis import api_errors


class Kraken:

    def __init__(self, client_id=None, client_secret=None):
        if not client_id and not os.environ.get("SALTY_TWITCH_CLIENT_ID", None):
            raise api_errors.AuthorizationRequiredError
        if not client_secret and not os.environ.get("SALTY_TWITCH_CLIENT_SECRET", None):
            raise api_errors.AuthorizationRequiredError

        self.twitch = Twitch(
            client_id or os.environ.get("SALTY_TWITCH_CLIENT_ID"),
            client_secret or os.environ.get("SALTY_TWITCH_CLIENT_SECRET")
        )

    def get_streams(self, channels):
        # Pass an array of channel you would like to retrieve stream objects for
        success = False
        response = {}
        try:
            response = self.twitch.get_streams(first=100, user_id=channels)
            success = True
        except TwitchAPIException as e:
            logging.error(e)

        return success, response

    # channel can be either string or list of strings
    def get_channels(self, channels):
        success = False
        response = {}
        try:
            response = self.twitch.get_channel_information(channels)
            success = True
        except TwitchAPIException as e:
            logging.error(e)

        return success, response
