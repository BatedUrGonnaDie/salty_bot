#! /usr/bin/evn python2.7

import datetime

import isodate
import pytz

HELP_TEXT = ["!uptime", "See how long the stream has been live for (must be live to get a time."]

def call(salty_inst, c_msg, **kwargs):
    if not salty_inst.is_live:
        return True, "Stream currently offline.  Follow to receive notifications for when I am."

    start = isodate.parse_datetime(salty_inst.stream_start)
    current = datetime.datetime.now(pytz.utc)
    return True, "The stream has been live for {0}.".format(str(current - start)[:-7])
