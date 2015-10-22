#! /usr/bin/env python2.7

def call(salty_inst, c_msg, **kwargs):
    users = c_msg["message"].split(" ")[1:]
    with open(salty_inst.blacklist_file, "a+") as fin:
        for i in users:
            if i not in salty_inst.blacklist:
                salty_inst.blacklist.append(i)
                fin.write("{0}\n".format(i))
            else:
                users.remove(i)
    return True, "{0} have been blacklisted.".format(", ".join(users))
