#! /usr/bin/env python3.7

HELP_TEXT = ["!song", "Contact batedurgonnadie to activate this in chat."]


def call(salty_inst, c_msg, **kwargs):
    success, response = salty_inst.newbs_api.get_song(c_msg["channel"][1:], **kwargs)
    if not success:
        return False, \
            "Error retrieving data from LoN ({0}).".format(response.status_code)

    response_string = f"Map: {response['mapName']} | DL: https://osu.ppy.sh/beatmapsets/{response['setId']}#osu/{response['mapId']} "

    return True, response_string


def test(salty_inst, c_msg, **kwargs):
    assert True
