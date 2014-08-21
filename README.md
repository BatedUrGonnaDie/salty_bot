Twitch chat bot with Twitch, Osu, YouTube, SRL, and LoL API integration.

Coded with Python 2.7.  Only required module is Requests.

Commands
========
`!commands` will output all of the active commands at the current time.

`!wr` will output the world record for the game and category.  Game is retrieved from Twitch API, and category is found
by matching the title against categories in the config file.  If one matches then it will print out that time.

`!leaderboards` will output the leaderboard for the game as specified in the config file.

`!race` will check to see if a variant of "race" is in your title to prevent spamming, and if it is it will check the
SRL API to see if you are in a race.  If you are listed in the race it will generate the game, category, and SRL nicks
racing, as well as output a multitwitch link if the race has 6 or fewer live racers, or an SRL race page link if it has
more to keep the link size down.

`!quote`/`!pun` will display a randomly selected quote/pun from a file.

`!addqoute`/`!addpun` will add the given quote/pun to a review file so that you can manually move it over later.  If 
the broadcaster uses this command the quote/pun will go straight into the live file (that means be careful).

`!rank` will retrieve the accuracy, pp ranking, level, and username of the streamer on osu.

`!createvote <loose/strict> "Poll Name" (option) (if) (strict)` will allow mods or channel host to create polls.  Only
one poll can be created at a time.  If strict you must specify options for viewers to vote for, if loose viewers may
vote for whatever they can think of.

`!vote <option>` will allow viewers to vote.  If poll is set to strict then viewers must input one of the options set
by the poll creator.

`!votes` will show what option is currently winning and how many votes it has.

`!endvote` will allow mods or channel host to close the current poll.

You can now make custom commands.  They must be one word commands and only have static text output.  You may also use
wildcards.  `$sender` and `$param` can be used and replaced with who sent the message and the first word after the
command respectively.  Currently the only way to add custom commands is to manually add them to the config file.

Channel Owner Commands
======================
`!blacklist` allows you to take away the ability for a user to use
commands.  Currently this will remove the ability to use the bot at all, so please be careful.

`!whitelist` will removes user from the blacklist.

`!review <quote/pun> <start>` to start reviewing your puns or quotes that have been added.  Bot will spit out the first
quote/pun in the file.
`!review <quote/pun> <approve/reject>` to confirm or deny the quote.  Note that currently there is no way to change the
text once it's in the file, so if formatting or capitalization is wrong, reject it and submit it correctly.
`!review <quote/pun> commit` to lock changes in place once all text has been reviewed.  Bot will prompt for this.

Passive Features
================
Ability to send you the maps posted in chat for osu directly in game.

Post the title and uploader of a youtube video posted in chat (can detect spam this way).

Insult people who don't know who トーボウ is (trigger can be changed to something else).

Ability to output static text every x amount of messages, or x amount of time, or both.  This can be useful for
different links to various social media.

Ability to set all commands as admin only.  This means that only your moderators will be able to use that command.
This can be useful to cut down on flood.

Ability to set flood limits on all commands.  Each command has its own flood limit, so you can use some more than
others.

Stuff That Happens In The Background
====================================
Passively retrieves game and title once per minute.

Passively watches for op messages to add mods to a mod list to allow for mod only commands.

If bot crashes for whatever reason it will automatically rejoin the channel in 1 minute or less.

Config File
===========
As soon as I decide on a permanent config file I will be posting an example one to model after, but at the moment it is
changing quite a bit.

Usage
=====
You can either download the bot (1 file) and make your own config file for the channels you want it to join
and commands to use, or shoot me an email at batedurgonnadie@yahoo.com and I can add you to my config file.  In the
future I hope to have a webpage up that will allow you to authenticate through twitch and customize the commands from
there.  If you're interested I will ask you all the necessary info needed to set you up and then all you have to do is
keep me updated with leaderboard/wr times.

License Thing?
==============
Do whatever you want with it except sell it or claim it to be your own unless you modify it.  Other than that have fun.
