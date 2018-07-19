#! /usr/bin/env python3.7

import json
import os

import pytest
import vcr

from modules import twitch_irc
from modules import saltybot
from modules import setup_env
from modules.extensions import regexes
from modules.commands.helpers import time_formatter
from modules.commands.helpers import get_category_string
from modules.commands.helpers import get_category_title
from modules.commands.helpers import get_diff_ratio
from modules.commands.helpers import get_suffix

os.environ["SALTY_ENVIRONMENT"] = "testing"
setup_env.set_environment_variables()
with open("tests/test_user.json", "r") as fin:
    config = json.load(fin)["1"]
SALTY_INST = saltybot.SaltyBot(config)


def test_irc_message_parsing():
    assert twitch_irc.TwitchIRC.extra_parse("@ban-reason=Follow\sthe\srules :tmi.twitch.tv CLEARCHAT #dallas :ronni") == {
        "tags": {"ban-reason": "Follow the rules"},
        "action": "CLEARCHAT",
        "params": ["#dallas", "ronni"],
        "prefix": ":tmi.twitch.tv",
        "channel": "#dallas",
        "raw": "@ban-reason=Follow\sthe\srules :tmi.twitch.tv CLEARCHAT #dallas :ronni"
    }


def test_time_parsing():
    assert "3:28:54" == time_formatter.format_time(12534)
    assert "3:54" == time_formatter.format_time(234)
    assert "5:00" == time_formatter.format_time(300)


def test_finding_category_from_string():
    assert (True, "Any%") == get_category_string.find_active_cat(
        {"Any%": "Any%", "Any% no WW": "Any% no WW"},
        "any%"
    )
    assert (False,
            "Could not find a category in the title that the user has a pb for.") == get_category_title.find_active_cat(
        {"Any%": "Any%", "120 Shines": "120 Shines"},
        "79 Shines"
    )


def test_finding_category_from_title():
    assert (True, "Any%") == get_category_title.find_active_cat(
        {"Any%": "Any%", "120 Shines": "120 Shines"},
        "Any% then 120 Shines later"
    )
    assert (True, "120 Shines") == get_category_title.find_active_cat(
        {"Any%": "Any%", "120 Shines": "120 Shines"},
        "120 Shines until pb then go hard in Any%"
    )
    assert (False,
            "Could not find a category in the title that the user has a pb for.") == get_category_title.find_active_cat(
        {"Any%": "Any%", "120 Shines": "120 Shines"},
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


def test_osu_regexes():
    assert regexes.OSU_URL.match("https://osu.ppy.sh/s/528824")
    assert regexes.OSU_URL.match("http://osu.ppy.sh/s/528824")
    assert regexes.OSU_URL.match("osu.ppy.sh/s/528824")
    assert regexes.OSU_URL.match("https://osu.ppy.sh/b/1121510")
    assert regexes.OSU_URL.match("http://osu.ppy.sh/b/1121510")
    assert regexes.OSU_URL.match("osu.ppy.sh/b/1121510")


def test_twitch_rate_limit():
    tirc = twitch_irc.TwitchIRC("test", "oauth:test")
    assert False is tirc.rate_limited
    tirc.sent_messages = 30
    assert True is tirc.rate_limited
    tirc.last_reset = 0
    tirc.clear_limit()
    assert False is tirc.rate_limited


def test_commands():
    for v in saltybot.command_functions.values():
        v.test("test", "test")
