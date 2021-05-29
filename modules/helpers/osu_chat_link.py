#! /usr/bin/env python3.7

import re

import modules.extensions.regexes as regexes
import modules.commands.helpers.time_formatter as time_formatter

ON_ACTION = "PRIVMSG"


def call(salty_inst, c_msg, balancer, **kwargs):
    beatmaps = re.findall(regexes.OSU_URL, c_msg["message"])
    final_list = []
    for i in beatmaps:
        success, response = salty_inst.osu_api.get_beatmap("s={0}&b={1}".format(i[0], i[1]), **kwargs)
        if not success:
            continue
        final_list.append("[{0}] {1} - {2}, mapped by {3} ({4} stars)".format(
            time_formatter.format_time(response[0]["total_length"]),
            response[0]["artist"],
            response[0]["title"],
            response[0]["creator"],
            round(float(response[0]["difficultyrating"]), 2)
        ))

    if len(final_list) == 0:
        return False, "No valid beatmaps linked."

    return True, " | ".join(final_list)
