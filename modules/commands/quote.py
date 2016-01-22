#! /usr/bin/env python2.7

from modules.commands.helpers.textutil import show as quote_show

def call(salty_inst, c_msg, **kwargs):
    success, response = quote_show(salty_inst, c_msg, "quote", **kwargs)
    return success, response
