#! /usr/bin/env python3.7

HELP_TEXT = ["!endvote", "Ends the current poll (broadcaster only unless mod enabled by broadcaster."]


def call(salty_inst, c_msg, **kwargs):
    if not salty_inst.config["settings"]["voting_mods"]:
        return False, "Only the broadcaster may end votes in this channel."
    votes = salty_inst.votes
    if not votes:
        return False, ""

    try:
        winning_amount = max(votes["options"].values())
        winning_keys = [votes["casing"][key] for key, value in votes["options"].items() if value == winning_amount]
        if len(winning_keys) == 0 or winning_amount == 0:
            return True, "No one voted for anything BibleThump"
        elif len(winning_keys) == 1:
            return True, "{0} has won with {1} votes.".format(winning_keys[0], winning_amount)
        else:
            return True, "{0} have tied with {1} votes!".format(
                ", ".join(winning_keys),
                winning_amount
            )
    finally:
        salty_inst.votes.clear()


def test(salty_inst, c_msg, **kwargs):
    assert True
