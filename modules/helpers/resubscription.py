#! /usr/bin/env python2.7

ON_ACTION = "USERNOTICE"

def call(salty_inst, c_msg, balancer, **kwargs):
    if not c_msg["tags"] and c_msg["tags"]["msg-id"] == "resub":
        return False, "Message is not a resubscription."
    if not salty_inst.config["settings"]["sub_message_active"]:
        return False, "Resubscription messages are off."
    if not salty_inst.config["settings"]["sub_message_resub"]:
        return False, "Resubscription message is blank."
    if int(c_msg["tags"]["room-id"]) != salty_inst.config["twitch_id"]:
        return False, "Resubscription is for hosted channel."

    msg = salty_inst.config["settings"]["sub_message_resub"]
    msg = msg.replace("$subscriber", c_msg["tags"]["display-name"])
    msg = msg.replace("$duration", "{0} months".format(c_msg["tags"]["msg-param-months"]))
    return True, msg
