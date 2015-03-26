Twitch chat bot with Twitch, Osu, YouTube, SRL, and LoL API integration.

Coded with Python 2.7.  Only required module is Requests.

Commands
========
`!commands` will output all of the active commands at the current time.

`!wr` outputs world record for a specific game.  Game and category can either be input by the user or can be implied
from the streamers game and title if they are live.

`!leaderboards` will output the game name escaped for speedrun.com leaderboards.

`!race` race/races/racing required in title to use.  Will poll the SRL API to check if the current streamer is in a
race, and if so output information about the race, and if the streamer has finished their time and place.

`!splits` will retrieve the best splits that you have uploaded to [splits.io](https://splits.io) for a game and
category.  A user, game, and category can be supplied or they can be inferred from the streamer, game, and title.

`!quote`/`!pun` will display a randomly selected quote/pun from a from the database.

`!addqoute`/`!addpun` will add the given quote/pun to a review file so that you can manually move it over later.  If
the broadcaster uses this command the quote/pun will go straight into the live file (that means be careful).

`!rank` will retrieve the accuracy, pp ranking, level, and username of the streamer on osu.

`!runes` will retrieve the active rune page and add up all the values.  Note that this will most likely break for the
runes with more than one stat.

`!masteries` will retrieve the active mastery page and output it like so, x/y/z.

`!createvote <loose/strict> "Poll Name" (option) (if) (strict)` will allow broadcaster to start a poll.  Mods can
start polls if the broadcaster has set so in their dashboard.  Loose means people can vote for anything while strict
means you must supply options for the users to vote for.

`!vote <option>` will allow viewers to vote.  If poll is set to strict then viewers must input one of the options set
by the poll creator.

`!checkvotes` will show what option is currently winning and how many votes it has.

`!endvote` will allow mods or channel host to close the current poll.

You can now make custom commands.  They must be one word commands and only have static text output.  You may also use
wildcards.  `$sender` and `$param` can be used and replaced with who sent the message and the first word after the
command respectively.  Currently the only way to add custom commands is to manually add them to the config file.

Channel Owner Commands
======================
`!blacklist <user>` adds the supplied user to a blacklist removing their ability to interact with the bot at all.

`!whitelist <user>` will remove said user from the blacklist.

`!review <quote/pun> <start>` to start reviewing your puns or quotes that have been added.  Bot will spit out the first
quote/pun in the file.
`!review <quote/pun> <approve/reject>` to confirm or deny the quote.  Note that currently there is no way to change the
text once it's in the file, so if formatting or capitalization is wrong, reject it and submit it correctly.
`!review <quote/pun> commit` to lock changes in place once all text has been reviewed.  Bot will prompt for this.

Passive Features
================
Ability to send you the osu maps posted in chat directly in game (useful if you have osu!direct).

Post the duration, title, uploaded, and views of a youtube video posted in chat (can detect spam this way).

Insult people who don't know who トーボウ is (trigger can be changed to something else).

Ability to output static text every x amount of messages, or x amount of time, or both.  This can be useful for
different links to various social media.

Ability to set all commands as moderator only.  This means that only your moderators will be able to use that command.
This can be useful to cut down on flood.

Ability to set flood limits on all commands.  Each command has its own flood limit, so you can use some more than
others.

Config File
===========
The config file is no more.  Please set up a postgres database with the following [schema](https://github.com/batedurgonnadie/salty_web).
If you are so inclined you can also set up the web side and have an interface to modify command settings.

Usage
=====
You can either download the bot (2 file) and make your own config file for the channels you want it to join
and commands to use, or shoot me an email at batedurgonnadie@yahoo.com and I can add you to my config file.  In the
future I hope to have a webpage up that will allow you to authenticate through twitch and customize the commands from
there.  If you're interested I will ask you all the necessary info needed to set you up and then all you have to do is
keep me updated with leaderboard/wr times.

License Thing?
==============
Do whatever you want with it except sell it or claim it to be your own unless you modify it.  Other than that have fun.
