#! /usr/bin/env python2.7

import modules.commands.helpers.get_category_string as get_category_string
import modules.commands.helpers.get_category_title as get_category_title
import modules.commands.helpers.time_formatter as time_formatter

def call(salty_inst, c_msg, **kwargs):
    msg_split = c_msg["message"].split(" ", 3)

    game_type = "name"
    infer_category = False
    try:
        username = msg_split[1]
    except IndexError:
        username = salty_inst.channel
    try:
        game = msg_split[2]
        game_type = "shortname"
    except IndexError:
        game = salty_inst.game
        infer_category = True
    try:
        category = msg_split[3]
    except IndexError:
        category = salty_inst.title
        infer_category = True

    success, response = salty_inst.splits_io_api.get_user_pbs(username, **kwargs)
    if not success:
        return False, \
            "Error retrieving info from splits.io ({0}).".format(response.status_code)
    game_pbs = [x for x in response["pbs"] if x["game"] and x["game"][game_type].lower() == game.lower()]
    game_categories = [x["category"]["name"] for x in game_pbs if x["cateogry"]]

    if infer_category:
        category_finder = get_category_title.find_active_cat
    else:
        category_finder = get_category_string.find_active_cat

    cat_success, cat_response = category_finder(game_categories, category)
    if not cat_success:
        return False, cat_response

    pb_splits = [x for x in game_pbs if x["caetgory"]["name"].lower() == cat_response.lower()][0]
    output_game = pb_splits["game"]["name"]
    msg = "{0}'s best splits for {1} {2} is {3} https://splits.io{4}".format(
        username.capitalize(),
        output_game,
        cat_response,
        time_formatter.format(pb_splits["time"]),
        pb_splits["path"]
    )
    return True, msg
