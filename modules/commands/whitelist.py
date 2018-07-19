#! /usr/bin/env python3.7

HELP_TEXT = ["!whitelist <name>", "[Broadcaster Only] Remove a user from the blacklist."]


def call(salty_inst, c_msg, **kwargs):
    users = c_msg["message"].split(" ")[1:]
    for i in users:
        try:
            salty_inst.blacklist.remove(i)
        except ValueError:
            users.remove(i)
    with open(salty_inst.blacklist_file, "w") as fin:
        fin.write("\n".join(salty_inst.blacklist))

    return True, "{0} have been whitelisted.".format(", ".join(users))


def test(salty_inst, c_msg, **kwargs):
    assert True
