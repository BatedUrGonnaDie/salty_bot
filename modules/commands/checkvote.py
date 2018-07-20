#! /usr/bin/env python3.7

HELP_TEXT = ["!checkvote", "Check the current results of a live poll."]


def call(salty_inst, c_msg, **kwargs):
    votes = salty_inst.votes
    if not votes:
        return False, "No open vote."

    response = 'Current poll: "{0}". '.format(votes["name"])
    if not votes["options"]:
        response += "No one has voted yet."
    else:
        response += "; ".join(
            ["{0}: {1}".format(votes["casing"][k], v) for k, v in list(votes["options"].items())]
        )

    return True, response


def test(salty_inst, c_msg, **kwargs):
    assert True
