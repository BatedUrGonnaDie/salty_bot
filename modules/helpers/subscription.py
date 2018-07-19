#! /usr/bin/env python3.7

ON_ACTION = "PRIVMSG"


def call(salty_inst, c_msg, balancer, **kwargs):
    if not salty_inst.config["settings"]["sub_message_active"]:
        return False, "Subscription messages are not active."
    if c_msg["sender"] != "twitchnotify":
        return False, "Not a subscription message."
    if len(c_msg["message"].split(" ")) > 3:
        return False, "Hosted subscription."

    msg = salty_inst.config["settings"]["sub_message_text"]
    msg = msg.replace("$subscriber", c_msg["message"].split(" ")[0])
    return True, msg
