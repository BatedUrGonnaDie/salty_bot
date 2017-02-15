#! /usr/bin/env python2.7

from modules.commands.helpers.textutil import get as get_pun

HELP_TEXT = ["!pun", "Displays a random reviewed pun from your channel."]

def call(salty_inst, c_msg, **kwargs):
    success, response = get_pun(salty_inst, c_msg, "pun", **kwargs)
    return success, response
