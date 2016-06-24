#! /usr/bin/env python2.7

def find_active_cat(game_categories, title):
    in_title = []
    position = {}
    title = title.lower()
    for k in game_categories.keys():
        if k.lower() in title:
            in_title.append(k)
            position[k] = title.find(k.lower())
    in_title = list(set(in_title))

    in_title_len = len(in_title)
    if in_title_len == 0:
        return False, "Could not find a category in the title that the user has a pb for."
    elif in_title_len == 1:
        return True, in_title[0]
    else:
        min_value = min(position.itervalues())
        min_keys = [x for x in position if position[x] == min_value]
        return True, sorted(min_keys, key=len)[-1]
