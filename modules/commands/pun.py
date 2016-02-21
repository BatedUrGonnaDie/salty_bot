#! /usr/bin/env python2.7

from modules.commands.helpers.textutil import get as get_pun

def call(salty_inst, c_msg, **kwargs):
    success, response = get_pun(salty_inst, c_msg, "pun", **kwargs)
    return success, response
