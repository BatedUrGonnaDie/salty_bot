Somewhat basic twitch chat bot with Twitch,Osu, Youtube, and SRL API's and soon LoL API integration.

Coded with Python 2.7.6.  Required module install Requests due to how many API calls it has now.

Aim of this bot is to be able to retrieve game playing for speedrunners to have rotating commands for different games.

Commands Explanation
====================
`!commands` will output all of the active commands at the current time.

`!wr` will simply output the world record for the game and category.  Game is retrieved from Twitch API, and category is found by matching the title against categories in the config file.  If one matches then it will print out that time.

`!leaderboards` will simply output the leaderboard for the game.

`!race` will check to see if a variant of race is in your title to prevent spamming, and if it is it will check the SRL API to see if you are in a race.  If you are listed in the race it will generate the game, category, and SRL nick racing, as well as output a mutltwitch link if the race has less than 6 races, and a SRL race page link if it has more to keep the link size down.

`!quote`/`!pun` will display a randomly selected quote/pun from a file.

`!addqoute`/`!addpun` will add the givin quote/pun to a review file so that you can manually move it over later.  If the broadcaster uses this command the quote/pun will go straight into the live file (that means be careful).  In the future you will be able to move them over through twitch chat so you don't have to do it manually.

`!song` will display the current song you are playing on osu if you have osu!np going and your game is set to Osu!, or it will output the current song you are listening to from a media player if you have something that can read the info from them (I use [SMG](http://obsproject.com/forum/threads/smg-now-playing.12744/) for this).  This command currently does not work due to the way that the bot is run now.  In the future I may set up an ftp server for this to work.

`!rank` will retrieve the accuracy, pp ranking, level, and username of the streamer.

`!bet` is meant for when you might throw the run away, but can easily be repurposed for a voting system (ie: what champion to play in LoL next).  
`!bets` will simply output what is currently wining.  
`!resetbets` will clear all bets and start over from scratch.
(All bet commands will be re-written as vote, but currently none are implemented yet.

Passive Features
================
Passively retrieves game and title from the Twitch API so you can just set it and go.

Ability to send you the maps posted in chat for osu directly in game.

Post the title and uploader of a youtube video posted in chat (can detect spam this way).

Usage
=====
You can either download the bot (1 file) and make your own config file for the channels you want it to join and commands to use, or for the time being shoot me an email at batedurgonnadie@yahoo.com and I can add you to my config file.  In the future I hope to have a webpage up that will allow you to authenticate through twitch and customize the commands from there.  If you're interested I will ask you all the necessary info needed.