#! /usr/bin/env python3.7

HELP_TEXT = ["!help <command>", "Displays help text for commands (<stuff> is required, <stuff?> is optional, exception is wr, splits, pb if you want later options all before must be present)."]


def call(salty_inst, c_msg, **kwargs):
    try:
        command = c_msg["message"].split(' ')[1]
    except IndexError:
        command = "help"

    try:
        command = "!{0}".format(command)
        help_list = salty_inst.commands[command]["help_text"]
    except KeyError:
        return False, "Invalid command: {0}".format(command)

    if help_list is None:
        return False, "No help text defined for {0}.".format(command)
    return True, \
        "Syntax: {0} | Description: {1}".format(help_list[0], help_list[1])


def test(salty_inst, c_msg, **kwargs):
    assert True
