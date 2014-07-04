Somewhat basic Twitch chat bot with Twitch, Osu, YouTube, SRL, and soon LoL API integration.

Coded with Python 2.7.6.  Required module install Requests due to how many API calls it has now.

Aim of this bot is to be able to retrieve game playing for speedrunners to have rotating commands for different games.

Commands Explanation
====================
`!commands` will output all of the active commands at the current time.

`!wr` will simply output the world record for the game and category.  Game is retrieved from Twitch API, and category is
found by matching the title against categories in the config file.  If one matches then it will print out that time.

`!leaderboards` will simply output the leaderboard for the game as specified in the config file.

`!race` will check to see if a variant of "race" is in your title to prevent spamming, and if it is it will check the
SRL API to see if you are in a race.  If you are listed in the race it will generate the game, category, and SRL nicks
racing, as well as output a multitwitch link if the race has 6 or fewer active racers, or an SRL race page link if it 
has more to keep the link size down.

`!quote`/`!pun` will display a randomly selected quote/pun from a file.

`!addqoute`/`!addpun` will add the given quote/pun to a review file so that you can manually move it over later.  If the
broadcaster uses this command the quote/pun will go straight into the live file (that means be careful).  In the future
you will be able to move them over through twitch chat so you don't have to do it manually.

`!review <type> <decision>` will allow you to review your quotes and puns through chat.  Use `start` for `<decision>`
and that will load them up into the dictionary.  From there you can use `approve` or `reject` to decide if you like
the text.  Once you have finished reviewing, use `commit` to save the changes to the live file.

`!song` will display the current song you are playing on osu if you have osu!np going and your game is set to Osu!, or
it will output the current song you are listening to from a media player if you have something that can read the info
from them (I use [SMG](http://obsproject.com/forum/threads/smg-now-playing.12744/) for this).  This command currently
does not work due to the way that the bot is run now.  In the future I may set up an ftp server for this to work.

`!rank` will retrieve the accuracy, pp ranking, level, and username of the streamer.

`!vote <vote_book> <your_vote>` will allow you to do much more than before.  If you are mod or broadcaster you can use
`<vote_book>` as createvote or removevote, which will create or remove the specified vote book respectively.  For normal
users you must put in both of these to enter your vote.  `!votes <optional vote_book>` will output all of the winning
votes for each vote category you input.  If category is specified it will only output the one supplied.


Passive Features
================
Ability to send you the maps posted in chat for osu directly in game.

Post the title and uploader of a youtube video posted in chat (can detect spam this way).

Insult people who don't know who トーボウ is.

Ability to output static text every x amount of messages, or x amount of time, or both.  This can be useful for
different links to various social media.

Ability to set all commands as admin only.  This means that only your moderators will be able to use that command.  This
can be useful to cut down on flood.

Ability to set flood limits on all commands.  Each command has its own flood limit, so you can use some more than
others.

Stuff That Happens In The Background
====================================
Passively retrieves game and title once per minute.  No more typing a command to retrieve it.  Should always be good to
go now.

Passively watches for op messages, and when it sees one it adds the user to an admin file.  This allows you to restrict
commands to being moderator only if you are so inclined.

Config File
===========
As soon as I decide on a permanent config file I will be posting an example one to model after, but at the moment it is
changing quite a bit.

Usage
=====
You can either download the bot (1 file) and make your own config file for the channels you want it to join and commands
to use, or shoot me an email at batedurgonnadie@yahoo.com and I can add you to my config file.  In the future I hope to
have a webpage up that will allow you to authenticate through twitch and customize the commands from there.  If you're
interested I will ask you all the necessary info needed to set you up and then all you have to do is keep me updated
with leaderboard/wr times.
