#! /usr/bin/env python3.7

import time

ON_ACTION = "PRIVMSG"


def call(salty_inst, c_msg, balancer, **kwargs):
    if not salty_inst.toobou["active"] and not salty_inst.toobou["output"]:
        return False, "Toobou not active or no output value."
    if c_msg["message"].lower().find(salty_inst.toobou["trigger"].lower()) == -1:
        return False, "Trigger not contained in PRIVMSG."
    if time.time() - salty_inst.toobou["limit"] < salty_inst.toobou["last"]:
        return False, "Toobou is still on cooldown."

    msg = salty_inst.toobou["output"]
    msg = msg.replace("$sender", c_msg["sender"])
    salty_inst.toobou["last"] = time.time()
    return True, msg.encode("utf-8")
