#! /usr/bin/env python2.7

from modules.commands.helpers.textutil import add as pun_add

HELP_TEXT = ["!addpun <pun>", "Add the selected text for review (broadcasters adding bypass review."]

def call(salty_inst, c_msg, **kwargs):
    success, response = pun_add(salty_inst, c_msg, "pun", **kwargs)
    return success, response

def test(salty_inst, c_msg, **kwargs):
    assert True
