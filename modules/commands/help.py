#! /usr/bin/env python2.7

help_text = {
    "help":         ["!help <command>", "Displays help text for commands (<stuff> is required, <stuff?> is optional, exception is wr, splits, pb if you want later options all before must be present)."],
    "blacklist":    ["!blacklist <name>", "[Broadcaster Only] Prevent a user from interacting with the bot in any way."],
    "whitelist":    ["!whitelist <name>", "[Broadcaster Only] Remove a user from the blacklist."],
    "commands":     ["!commands", "Displays all active commands in the current channel."],
    "quote":        ["!quote", "Displays a random reviewed quote from your channel."],
    "addquote":     ["!addquote <quote>", "Add the selected text for review (broadcasters adding bypass review."],
    "pun":          ["!pun", "Displays a random reviewed pun from your channel."],
    "addpun":       ["!addpun <pun>", "Add the selected text for review (broadcasters adding bypass review."],
    "8ball":        ["!8ball <question>", "Ask the 8ball and get a response."],
    "uptime":       ["!uptime", "See how long the stream has been live for (must be live to get a time."],
    "highlight":    ["!highlight <message?>", "Save a timestamp with optional message decscribing what you wanted to highlight."],
    "show_highlight": ["!show_highlight", "[Broadcaster Only] Lists all highlights saved to this point and clears the queue."],
    "wr":           ["!wr <game shortcode?> <category?>", "Retrieve the world record for a game's category.  Will try to use game and title if stream is live, otherwise parameters are required."],
    "pb":           ["!pb <user?> <game shortcode?> <category?>", "Retrieve users pb for a game's category.  Will try to use game and title if stream is live, otherwise parameters are required."],
    "leaderboard":  ["!leaderboard", "Adds Twitch game to speedrun.com url, may or may not work depending on how games are mad on speedrun.com"],
    "splits":       ["!splits <user?> <game?> <category?>", "Retrive pb splits from splits.io.  Will try and user game and category from title and streamer if live, else all are required."],
    "race":         ["!race", "Retrieve race information from speedrdunslive.com"],
    "song":         ["!song", "Contact batedurgonnadie to activate this in chat."],
    "rank":         ["!rank <user?>", "Retrieve basic information about an osu user."],
    "runes":        ["!runes", "[Game: LoL] Retrieve users current rune book and stats from said runes."],
    "masteries":    ["!masteries", "[Game: LoL] Retrieve mastery page and how they are distributed."]
}

def call(salty_inst, c_msg, **kwargs):
    try:
        command = c_msg["message"].split(' ')[1]
    except IndexError:
        command = "help"

    try:
        help_list = help_text[command]
    except KeyError:
        return False, "Invalid command: {0}".format(command)

    return True, \
        "Syntax: {0} | Description: {1}".format(help_list[0], help_list[1])
