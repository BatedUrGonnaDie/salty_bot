#! /usr/bin/evn python2.7

import datetime

import isodate
import pytz

HELP_TEXT = ["!highlight <message?>", "Save a timestamp with optional message decscribing what you wanted to highlight."]

def call(salty_inst, c_msg, **kwargs):
    if not salty_inst.is_live:
        return True, "You can only highlight while the stream is live."

    try:
        if c_msg["sender"] == salty_inst.channel and c_msg["message"].split(" ", 2)[1]:
            param = c_msg["message"].split(" ", 2)[1]
            if param == "show":
                msg = "Things you should highlight: "
                for i in salty_inst.highlights:
                    msg += "{0} @ {1}, ".format(i["desc"], i["time"])
                return True, msg[:-2]
    except IndexError:
        pass

    current = datetime.datetime.now(pytz.utc)
    start = isodate.parse_datetime(salty_inst.stream_start)
    msg = c_msg["message"].split("hightlight")[-1]
    salty_inst.highlights.append({"time" : str(current - start)[:-7], "desc" : msg})
    return True, \
        "Current time added to the highlight queue. {0}: use !highlight show to view the highlights saved.".format(
            salty_inst.channel
        )

def test(salty_inst, c_msg, **kwargs):
    assert True
