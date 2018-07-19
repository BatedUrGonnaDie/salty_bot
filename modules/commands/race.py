#! /usr/bin/env python3.7

import time

from modules.commands.helpers import time_formatter
from modules.commands.helpers import get_suffix

HELP_TEXT = ["!race", "Retrieve race information from speedrdunslive.com"]

def call(salty_inst, c_msg, **kwargs):
    channel = salty_inst.channel
    success, response = salty_inst.srl_api.get_races(**kwargs)
    if not success:
        return False, \
            "Error retrieving data for SRL API ({0}).".format(response.status_code)

    races = response["races"]
    for i in races:
        if channel in [x["twitch"].lower() for x in list(i["entrants"].values())]:
            race_channel = i
            break
    else:
        return False, "User not currently in a race."

    entrants = []
    for k, v in race_channel["entrants"].items():
        if salty_inst.channel == v["twitch"].lower():
            real_nick = k
        if v["statetext"] == "Ready" or v["statetext"] == "Entered":
            if v["twitch"] != "":
                entrants.append(k)

    user_place = race_channel["entrants"][real_nick]["place"]
    user_time = race_channel["entrants"][real_nick]["time"]
    race_status = race_channel["statetext"]
    race_time = race_channel["time"]
    race_link = "http://speedrunslive.com/race/?id={}".format(race_channel["id"])

    success, response = salty_inst.twitch_api.get_streams(entrants)
    if success:
        live_entrants = [x["channel"]["name"] for x in response["streams"]]
    else:
        live_entrants = []

    send_msg = "Game: {0}, Category: {1}, Status: {2}".format(
        race_channel["game"]["name"], race_channel["goal"], race_status)
    if race_time > 0:
        if user_time > 0:
            time_formatted = time_formatter.format_time(user_time)
            send_msg += ", Finished {0}{1} with a time of {2}".format(
                user_place, get_suffix.suffix(user_place), time_formatted)
        else:
            time_formatted = time_formatter.format_time(time.time() - race_time)
            send_msg += ", RaceBot Time: {0}".format(time_formatted)
    if race_status == "Complete":
        send_msg += ". {}".format(race_link)
    elif len(live_entrants) <= 6 and len(live_entrants) > 1:
        multi_link = "http://kadgar.net/live/{0}".format("/".join(live_entrants))
        send_msg += ". {0}".format(multi_link)
    else:
        send_msg += ". {}".format(race_link)
    return True, send_msg


def test(salty_inst, c_msg, **kwargs):
    assert True
