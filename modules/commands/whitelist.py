#! /usr/bin/env python2.7

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
