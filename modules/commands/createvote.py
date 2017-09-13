#! /usr/bin/env python2.7

import re

from modules.extensions import regexes

HELP_TEXT = ['!createvote <loose/strict> "Poll Name" (options) (if) (strict)', "Create a new poll. Loose means any votes count, strict only can vote for supplied options. Format with quotes and parenthesis."]

def call(salty_inst, c_msg, **kwargs):
    if not salty_inst.config["settings"]["voting_mods"]:
        return False, "Only the broadcast may create polls in this channel."
    if salty_inst.votes:
        return False, "There is already a poll in progress."
    try:
        poll_type = c_msg["message"].split(" ")[1].lower()
    except IndexError:
        return False, "Please enter the type of poll: loose/strict."
    try:
        poll_name = re.findall(regexes.POLL_NAME, c_msg["message"])[0]
    except IndexError:
        return False, "Please enter a name for the poll surronded by quotes."

    salty_inst.votes = {
        "name" : poll_name,
        "type" : poll_type,
        "options" : {},
        "casing" : {},
        "voters" : {}
    }

    if poll_type == "strict":
        options = re.findall(regexes.POLL_OPTIONS, c_msg["message"])
        if not options:
            salty_inst.votes.clear()
            return False, "Please supply options for a strict poll surronded by parenthesis."

        options = [x.strip() for x in options]
        for i in options:
            salty_inst.votes["options"][i.lower()] = 0
            salty_inst.votes["casing"][i.lower()] = i
        return True, "You may now vote for {0} with the following options: {1}.".format(
            poll_name,
            ", ".join(options)
        )
    elif poll_type == "loose":
        return True, "You may now vote for {0} with any options you wish.".format(poll_name)
    else:
        salty_inst.votes.clear()
        return False, "Invalid poll type, only strict/loose accepted."

def test(salty_inst, c_msg, **kwargs):
    assert True
