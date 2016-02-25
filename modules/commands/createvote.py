#! /usr/bin/env python2.7

import re

from modules.extensions import regexes

def call(salty_inst, c_msg, **kwargs):
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
            return False, "Please supply options for a strict poll surronded by parenthesis."

        for i in options:
            salty_inst.votes["options"][i.lower()] = 0
            salty_inst.votes["casing"][i.lower()] = i
        return True, "You may now vote for {0} with the following options: {1}.".format(
            poll_name,
            ", ".join(options)
        )
    elif poll_type == "loose":
        return True, "You may now vote for {0} with any options you wish.".format(", ".join(options))
    else:
        return False, "Invalid poll type, only strict/loose accepted."
