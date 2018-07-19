#! /usr/bin/env python3.7

HELP_TEXT = ["!vote <poll option>", "Places a vote in the poll."]


def call(salty_inst, c_msg, **kwargs):
    if not salty_inst.votes:
        return False, ""
    try:
        sender_vote = c_msg["message"].split(" ", 1)[-1]
        vote_lower = sender_vote.lower()
    except Exception:
        return False, ""

    if vote_lower.strip() == "!vote":
        return False, "Please suuply an option to vote for."

    if salty_inst.votes["type"] == "strict":
        if vote_lower not in salty_inst.votes["options"]:
            return False, "You must vote for one of the following options: {0}".format(
                ", ".join(list(salty_inst.votes["options"].keys()))
            )

    if c_msg["sender"] in salty_inst.votes["voters"]:
        previous_vote = salty_inst.votes["voters"][c_msg["sender"]]
        if vote_lower == previous_vote:
            return False, ""
        salty_inst.votes["options"][previous_vote] -= 1
        if salty_inst.votes["options"][previous_vote] == 0 and salty_inst.votes["type"] == "loose":
            del salty_inst.votes["options"]["previous"]

        try:
            salty_inst.votes["options"][vote_lower] += 1
        except KeyError:
            salty_inst.votes["options"][vote_lower] = 1

        salty_inst.votes["voters"][c_msg["sender"]] = vote_lower
        return True, "{0} has changed their vote to {1}.".format(
            c_msg["sender"],
            vote_lower
        )
    else:
        try:
            salty_inst.votes["options"][vote_lower] += 1
        except KeyError:
            salty_inst.votes["options"][vote_lower] = 1

        salty_inst.votes["voters"][c_msg["sender"]] = vote_lower
        return True, "{0} now has {1} votes.".format(
            vote_lower,
            str(salty_inst.votes["options"][vote_lower])
        )


def test(salty_inst, c_msg, **kwargs):
    assert True
