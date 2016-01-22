#! /usr/bin/env python2.7

import modules.commands.helpers.get_category_string as get_category_string
import modules.commands.helpers.get_category_title as get_category_title
import modules.commands.helpers.time_formatter as time_formatter

def call(salty_inst, c_msg, **kwargs):
    msg_split = c_msg["message"].split(" ", 2)
    infer_category = True
    search_game = True

    try:
        game = msg_split[1].lower()
        search_game = False
    except IndexError:
        game = salty_inst.game
    try:
        category = msg_split[2].lower()
        infer_category = False
    except IndexError:
        category = salty_inst.title

    if search_game:
        success, response = salty_inst.sr_com_api.get_search_games(game)
        if not success:
            return False, \
                "Error retrieving info from speedrun.com ({0}).".format(response.status_code)
    else:
        success, response = salty_inst.sr_com_api.get_game_leaderboards(game, category, )
