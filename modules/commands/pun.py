#! /usr/bin/env python2.7

from modules.commands.helpers.textutil import show as pun_show

def call(salty_inst, c_msg, **kwargs):
    success, response = pun_show(salty_inst, c_msg, "pun", **kwargs)
    return success, response
