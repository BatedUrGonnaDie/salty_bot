#! /usr/bin/env python2.7

from modules.commands.helpers.textutil import get as get_quote

HELP_TEXT = ["!quote", "Displays a random reviewed quote from your channel."]

def call(salty_inst, c_msg, **kwargs):
    success, response = get_quote(salty_inst, c_msg, "quote", **kwargs)
    return success, response
