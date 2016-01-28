#! /usr/bin/env python2.7

import re

import isodate

import modules.extensions.regexes as regexes
import modules.commands.helpers.time_formatter as time_formatter

def call(salty_inst, c_msg, **kwargs):
    video_ids = re.findall(regexes.YOUTUBE_URL, c_msg["message"])
    if not video_ids:
        return
    seen_ids = set()
    seen_add = seen_ids.add
    video_ids = [x for x in video_ids if not (x in seen_ids or seen_add(x))]
    parts = ["snippet", "statistics", "contentDetails"]
    final_list = []
    success, response = salty_inst.youtube_api.get_videos(video_ids, parts, **kwargs)
    if not success:
        return False, \
            "Error retrieving info from youtube API ({0})".format(response.status_code)

    if len(response["items"]) == 0:
        return False, "No valid ID's found."

    for i in response["items"]:
        final_list.append("[{0}] {1} uploaded by {2}. Views: {3}".format(
            time_formatter.format(isodate.parse_duration(i["contentDetails"]["duration"])),
            i["snippet"]["title"].encode("utf-8"),
            i["snippet"]["channelTitle"].encode("utf-8"),
            i["statistics"]["viewCount"]
        ))
    return " | ".join(final_list)
