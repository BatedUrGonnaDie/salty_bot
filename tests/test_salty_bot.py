#! /usr/bin/env python2.7

import pytest

from modules import irc
from modules import twitch_irc

from modules.commands.helpers import time_formatter
from modules.commands.helpers import get_category_string
from modules.commands.helpers import get_category_title

def test_irc_message_parsing():
    assert 1

def test_time_parsing():
    assert "3:28:54" == time_formatter.format_time(12534)
    assert "3:54" == time_formatter.format_time(234)
    assert "5:00" == time_formatter.format_time(300)

def test_finding_category_from_string():
    assert (True, "Any%") == get_category_title.find_active_cat(
        {"Any%" : "Any%", "120 Shines" : "120 Shines"},
        "Any% then 120 Shines later"
    )
    assert (True, "120 Shines") == get_category_title.find_active_cat(
        {"Any%" : "Any%", "120 Shines" : "120 Shines"},
        "120 Shines until pb then go hard in Any%"
    )
