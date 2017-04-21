#! /usr/bin/env python2.7

import json

import pytest
import vcr

from modules import irc
from modules import twitch_irc
from modules import saltybot
from modules import setup_env
from modules.commands.helpers import time_formatter
from modules.commands.helpers import get_category_string
from modules.commands.helpers import get_category_title
from modules.commands.helpers import get_diff_ratio
from modules.commands.helpers import get_suffix


def test_irc_message_parsing():
    assert 1
    assert 1

def test_time_parsing():
    assert "3:28:54" == time_formatter.format_time(12534)
    assert "3:54" == time_formatter.format_time(234)
    assert "5:00" == time_formatter.format_time(300)

def test_finding_category_from_string():
    assert (True, "Any%") == get_category_string.find_active_cat(
        {"Any%" : "Any%", "Any% no WW" : "Any% no WW"},
        "any%"
    )
    assert (False, "Could not find a category in the title that the user has a pb for.") == get_category_title.find_active_cat(
        {"Any%" : "Any%", "120 Shines" : "120 Shines"},
        "79 Shines"
    )

def test_finding_category_from_title():
    assert (True, "Any%") == get_category_title.find_active_cat(
        {"Any%" : "Any%", "120 Shines" : "120 Shines"},
        "Any% then 120 Shines later"
    )
    assert (True, "120 Shines") == get_category_title.find_active_cat(
        {"Any%" : "Any%", "120 Shines" : "120 Shines"},
        "120 Shines until pb then go hard in Any%"
    )
    assert (False, "Could not find a category in the title that the user has a pb for.") == get_category_title.find_active_cat(
        {"Any%" : "Any%", "120 Shines" : "120 Shines"},
        "68 Shines until pb then go hard in Ruppee%"
    )

def test_get_diff_ratio():
    assert get_diff_ratio.diff_ratio("120 Shines", "79 Shines") > .6
    assert get_diff_ratio.diff_ratio("79 Ruppees", "79 Shines") < .6

def test_get_suffix():
    assert "th" == get_suffix.suffix(11)
    assert "st" == get_suffix.suffix(1)
    assert "nd" == get_suffix.suffix(2)
    assert "rd" == get_suffix.suffix(3)
    assert "th" == get_suffix.suffix(4)
