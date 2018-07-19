#! /usr/bin/env python3.7

from modules.commands.helpers.textutil import add as quote_add

HELP_TEXT = ["!addquote <quote>", "Add the selected text for review (broadcasters adding bypass review."]


def call(salty_inst, c_msg, **kwargs):
    success, response = quote_add(salty_inst, c_msg, "quote", **kwargs)
    return success, response


def test(salty_inst, c_msg, **kwargs):
    assert True
