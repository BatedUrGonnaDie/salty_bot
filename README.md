**WARNING**  
Salty is currently going through a complete rewrite with a lot of complete
API breaking changes.  If you are basing a bot off of this project functions
may change at any time

The changes that are in the future rewrite have not been tested in any form
and will not be used until proper tests have been written.  
**WARNING**

Twitch chat bot with Twitch, Osu, YouTube, SRL, and LoL API integration.

Coded with Python 3.7.  Dependencies are located in requirements.txt.

Commands
========
`!commands` will output all of the active commands at the current time.

`!wr <game shortcode?> <category?>` outputs world record for a specific game.  Game and category can either be input by the user or can be implied
from the streamers game and title if they are live.

`!pb <user?> <game shortcode?> <category?>` the pb for the specified user.  If category and game is omitted it will attempt
to infer them from the current streamer's game/title.  If user is also omitted it will assume the streamer.

`!leaderboards` will output the game name escaped for speedrun.com leaderboards.

`!race` race/races/racing required in title to use.  Will poll the SRL API to check if the current streamer is in a
race, and if so output information about the race, and if the streamer has finished their time and place.

`!splits <user?> <game shortcode?> <category?>` will retrieve the best splits that you have uploaded to [splits.io](https://splits.io) for a game and
category.  A user, game, and category can be supplied or they can be inferred from the streamer, game, and title.

`!quote`/`!pun` will display a randomly selected quote/pun from a from the database.

`!addqoute`/`!addpun` will add the given quote/pun to a review file so that you can manually move it over later.  If
the broadcaster uses this command the quote/pun will go straight into the live file (that means be careful).

`!rank <user?>` will retrieve the accuracy, pp ranking, level, and username
of the streamer (or the user specified) on osu.

`!createvote <loose/strict> "Poll Name" (option) (if) (strict)` will allow broadcaster to start a poll.  Mods can
start polls if the broadcaster has set so in their dashboard.  Loose means people can vote for anything while strict
means you must supply options for the users to vote for.

`!vote <option>` will allow viewers to vote.  If poll is set to strict then viewers must input one of the options set
by the poll creator.

`!checkvotes` will show what option is currently winning and how many votes it has.

`!endvote` will allow mods or channel host to close the current poll.

`!uptime` will display how long the current stream has been live for.

You can now make custom commands.  They must be one word commands and only have static text output.  You may also use
wildcards.  `$sender` and `$param` can be used and replaced with who sent the message and the first word after the
command respectively.

Channel Owner Commands
======================
`!blacklist <user>` adds the supplied user to a blacklist removing their ability to interact with the bot at all.

`!whitelist <user>` will remove said user from the blacklist.

`!addcom <trigger> <limit> <admin> <output>` will add the given custom command to the bot.

`!delcom <trigger>` will delete the command from the bot.  Please do not include the '!' when specifying a trigger.

Passive Features
================
Ability to send you the osu maps posted in chat directly in game (useful if you have osu!direct).

Post the duration, title, uploaded, and views of a youtube video posted in chat (can detect spam this way).

Insult people who don't know who トーボウ is (trigger can be changed to something else).

Ability to output static text every x amount of messages, or x minutes, or both.  This can be useful for
different links to various social media.

All commands can be limited to moderators only and each command has its own rate limiting.

Running Locally
===============
Copy the default config file and fill out appropriately, and then rename to `general_config.json`.
Set up a postgres database with the following [schema](https://github.com/BatedUrGonnaDie/salty_web/blob/master/db/schema.rb).
If you want a web interface to change settings then you must follow the set up directions at
[the web repo](https://github.com/batedurgonnadie/salty_web).
