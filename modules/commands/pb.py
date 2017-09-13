#! /usr/bin/env python2.7

from modules.commands.helpers import get_category_string
from modules.commands.helpers import get_category_title
from modules.commands.helpers import time_formatter
from modules.commands.helpers import get_suffix

HELP_TEXT = ["!pb <user?> <game shortcode?> <category?>", "Retrieve users pb for a game's category.  Will try to use game and title if stream is live, otherwise parameters are required."]

def call(salty_inst, c_msg, **kwargs):
    msg_split = c_msg["message"].split(" ", 3)
    infer_category = True

    try:
        user_name = msg_split[1].lower()
    except IndexError:
        user_name = salty_inst.speedruncom_nick
    try:
        game = msg_split[2].lower()
    except IndexError:
        game = salty_inst.game
    try:
        category = msg_split[3].lower()
        infer_category = False
    except IndexError:
        category = salty_inst.title

    success, response = salty_inst.sr_com_api.get_user_pbs(user_name, ["game", "category"], **kwargs)
    if not success:
        return False, \
            "Error retrieving pbs from speedrun.com ({0}).".format(response.status_code)

    found_categories = []
    matching_games = []
    for i in response["data"]:
        if game == i["game"]["data"]["abbreviation"] or game == i["game"]["data"]["names"]["international"].lower():
            found_categories.append(i["cateory"]["data"]["name"])
            matching_games.append(i)
            break
    else:
        return False, "Could not find a pb for {0}.".format(game)

    if infer_category:
        category_finder = get_category_title.find_active_cat
    else:
        category_finder = get_category_string.find_active_cat

    cat_success, cat_response = category_finder(found_categories, category)
    if not cat_success:
        return False, cat_response

    for i in matching_games:
        if i["category"]["data"]["name"] == cat_response:
            pb_record = i

    pb_time = time_formatter.format_time(i["run"]["times"]["primary_t"])
    place = "{0}{1}".format(str(pb_record["place"]), get_suffix.suffix(pb_record["place"]))
    msg = "{0}'s pb for {1} {2} is {3}.  They are ranked {4} on speedrun.com {5}".format(
        user_name.capitalize(),
        pb_record["game"]["data"]["names"]["international"],
        cat_response,
        pb_time,
        place,
        pb_record["run"]["weblink"]
    )

    return True, msg

def test(salty_inst, c_msg, **kwargs):
    assert True
