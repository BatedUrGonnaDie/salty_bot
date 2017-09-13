#! /usr/bin/env python2.7

HELP_TEXT = ["!rank <user?>", "Retrieve basic information about an osu user."]

def call(salty_inst, c_msg, **kwargs):
    try:
        user = c_msg["message"].split("rank ")[1]
    except IndexError:
        user = ""
    osu_nick = user or c_msg["channel"][1:]
    success, response = salty_inst.osu_api.get_user(osu_nick, **kwargs)
    if not success:
        return False, "Error retrieving user from osu api ({})."\
            .format(response.status_code)
    try:
        response = response[0]
    except IndexError:
        return False, "No users found with name: {0}.".format(osu_nick)
    msg = "{} is level {} with {}% accuracy and ranked {}.".format(
        response["username"],
        int(round(float(response["level"]))),
        round(float(response["accuracy"]), 2),
        "{:,}".format(int(response["pp_rank"]))
    )
    return True, msg

def test(salty_inst, c_msg, **kwargs):
    assert True
