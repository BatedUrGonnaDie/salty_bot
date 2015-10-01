#! /usr/bin/env python2.7

def call(c_msg, **kwargs):
    try:
        user = c_msg["message"].split("rank ")[1]
    except IndexError:
        user = ""
    osu_nick = user or c_msg["channel"][1:]
    success, response = kwargs["osu_api"].get_user(osu_nick)
    if not success:
        return False, "Error retrieving user from osu api ({})."\
            .format(response.status_code)
    msg = "{} is level {} with {}% accuracy and ranked {}."\
        .format(response["username"],
                int(round(float(response["level"]))),
                round(float(response["accuracy"]), 2),
                "{:,}".format(int(response["pp_rank"])))
    return True, msg
