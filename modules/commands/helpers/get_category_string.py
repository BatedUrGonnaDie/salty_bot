#! /usr/bin/env

import modules.commands.helpers.get_diff_ratio as get_diff_ratio

def find_active_cat(game_categories, user_string):
    for k in game_categories.keys():
        if k.lower() == user_string.lower():
            return True, k

    best_ratio = {}
    for i in game_categories:
        best_ratio[i] = get_diff_ratio.diff_ratio(user_string.lower(), i.lower())

    try:
        return True, max(best_ratio, key=best_ratio.get)
    except ValueError:
        return False, "Could not find pb with close enough match to {0}".format(user_string)
